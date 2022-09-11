import logging
import sqlalchemy.orm
import nio.store.database

log = logging.getLogger(__name__)

from lokiunimore.matrix.database import engine
from lokiunimore.matrix.templates.messages import WELCOME_MESSAGE_TEXT, WELCOME_MESSAGE_HTML, SUCCESS_MESSAGE_TEXT, SUCCESS_MESSAGE_HTML, GOODBYE_MESSAGE_TEXT, GOODBYE_MESSAGE_HTML, UNLINK_MESSAGE_TEXT, UNLINK_MESSAGE_HTML
from lokiunimore.matrix.client_class import ExtendedAsyncClient, RequestError
from lokiunimore.matrix.event_filtering import filter_processed_events
from lokiunimore.config import MATRIX_HOMESERVER, MATRIX_USER_ID, MATRIX_STORE_DIR, MATRIX_PUBLIC_SPACE_ID, MATRIX_PRIVATE_SPACE_ID, FLASK_BASE_URL
from lokiunimore.sql.tables import MatrixUser


client = ExtendedAsyncClient(
    homeserver=MATRIX_HOMESERVER.__wrapped__,
    user=MATRIX_USER_ID.__wrapped__,
    store_path=str(MATRIX_STORE_DIR.__wrapped__),
    config=nio.AsyncClientConfig(
        store_sync_tokens=True,
        store=nio.store.database.DefaultStore,
    ),
)
"""
The bot's Matrix client, powered by :mod:`nio`.
"""


@filter_processed_events
async def on_member(room: nio.MatrixRoom, event: nio.Event):
    """
    Callback for when a :class:`nio.RoomMemberEvent` is received.
    """

    # Filters allow us to determine the event type in a better way
    event: nio.InviteMemberEvent | nio.RoomMemberEvent

    # Catch events about myself immediately
    if event.state_key == client.user_id:
        # If I'm invited to a room, join it
        if event.membership == "invite":
            await join_when_invited(room)

    elif event.membership == "join":
        # If somebody joins the parent space, notify them of my presence and send them their profile URL
        if room.room_id == MATRIX_PUBLIC_SPACE_ID:
            await handle_public_space_joiner(event.state_key)
        # If somebody joins the child space, notify them of the successful login
        elif room.room_id == MATRIX_PRIVATE_SPACE_ID:
            await handle_private_space_joiner(event.state_key)

    elif event.membership == "leave":
        # If somebody leaves the parent space, remove them from all subrooms, delete their account, and finally notify them
        if room.room_id == MATRIX_PUBLIC_SPACE_ID:
            await handle_public_space_leaver(event.state_key)
        # If somebody leaves the child space, remove them from all subrooms, delete their linking, and finally notify them
        elif room.room_id == MATRIX_PRIVATE_SPACE_ID:
            await handle_private_space_leaver(event.state_key)

    elif event.membership == "ban":
        # TODO: If somebody is banned from the parent space... propagate the ban?
        if room.room_id == MATRIX_PUBLIC_SPACE_ID:
            await handle_public_space_leaver(event.state_key)
        # TODO: If somebody is banned from the child space... propagate the ban?
        elif room.room_id == MATRIX_PRIVATE_SPACE_ID:
            await handle_private_space_leaver(event.state_key)


async def join_when_invited(room: nio.MatrixRoom):
    log.debug(f"Received invite to: {room.room_id}")
    await client.join(room.room_id)
    log.info(f"Accepted invite to: {room.room_id}")


async def handle_public_space_joiner(user_id: str):
    log.debug(f"User joined public space: {user_id}")

    log.debug(f"Creating MatrixUser for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user = MatrixUser(id=user_id)
        matrix_user = session.merge(matrix_user)
        session.commit()
        log.debug(f"Created MatrixUser for: {user_id}")
        token = matrix_user.token

    log.debug(f"Notifying user of the account creation: {user_id}")
    formatting = dict(
        username_text=client.user_id,
        username_html=await client.mention_html(user_id),
        base_url=FLASK_BASE_URL,
        token=token,
    )
    await client.room_send_message_html(
        await client.find_or_create_pm_room(user_id),
        text=WELCOME_MESSAGE_TEXT.format(**formatting),
        html=WELCOME_MESSAGE_HTML.format(**formatting)
    )
    log.debug(f"Notified user of the account creation: {user_id}")

    log.info(f"Handled joiner of public space: {user_id}")


async def handle_private_space_joiner(user_id: str):
    log.info(f"User joined private space: {user_id}")

    log.debug(f"Setting MatrixUser as joined for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
        matrix_user.joined_private_space = True
        session.commit()
        log.debug(f"Set MatrixUser as joined for: {user_id}")
        token = matrix_user.token

    log.debug(f"Notifying user of the account link: {user_id}")
    formatting = dict(
        base_url=FLASK_BASE_URL,
        token=token,
    )
    await client.room_send_message_html(
        await client.find_or_create_pm_room(user_id),
        text=SUCCESS_MESSAGE_TEXT.format(**formatting),
        html=SUCCESS_MESSAGE_HTML.format(**formatting)
    )
    log.debug(f"Notified user of the account link: {user_id}")

    log.info(f"Handled joiner of private space: {user_id}")


async def handle_public_space_leaver(user_id: str):
    log.info(f"User left public space: {user_id}")

    log.debug(f"Deleting MatrixUser for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
        if matrix_user is None:
            log.warning(f"User left public space without having a pre-existent record in the db: {user_id}")
        else:
            if matrix_user.account is not None and len(matrix_user.account.matrix_users) == 1:
                session.delete(matrix_user.account)
            session.delete(matrix_user)
            session.commit()
            log.debug(f"Deleted MatrixUser for: {user_id}")

    log.debug(f"Notifying user of the account deletion: {user_id}")
    await client.room_send_message_html(
        await client.find_or_create_pm_room(user_id),
        text=GOODBYE_MESSAGE_TEXT,
        html=GOODBYE_MESSAGE_HTML
    )
    log.debug(f"Notified user of the account deletion: {user_id}")

    log.debug(f"Finding room hierarchy of the public space...")
    hierarchy = await client.room_hierarchy(MATRIX_PUBLIC_SPACE_ID.__wrapped__, max_depth=9, suggested_only=False)

    log.debug(f"Removing public space leaver from {len(hierarchy)} rooms: {user_id}")
    success_count = 0
    for room in hierarchy:
        room_id = room["room_id"]
        try:
            await client.room_kick(room_id=room_id, user_id=user_id, reason="Left parent space")
        except RequestError as e:
            log.warning(f"Could not remove public space leaver {user_id} from {room_id}: {e!r}")
        else:
            success_count += 1
    log.debug(f"Removed public space leaver from {success_count} rooms: {user_id}")

    log.info(f"Handled leaver of public space: {user_id}")


async def handle_private_space_leaver(user_id: str):
    log.debug(f"User left private space: {user_id}")

    log.debug(f"Unlinking account for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
        if matrix_user is None:
            log.warning(f"User left private space without having a pre-existent record in the db: {user_id}")
        elif matrix_user.account is None:
            log.warning(f"User left private space without having a linked account in the db: {user_id}")
            token = matrix_user.token
        else:
            if len(matrix_user.account.matrix_users) == 1:
                session.delete(matrix_user.account)
            matrix_user.account = None
            matrix_user.joined_private_space = False
            session.commit()
            log.debug(f"Unlinked account for: {user_id}")
            token = matrix_user.token

    log.debug(f"Notifying user of the account unlinking: {user_id}")
    formatting = dict(
        base_url=FLASK_BASE_URL,
        token=token,
    )
    await client.room_send_message_html(
        await client.find_or_create_pm_room(user_id),
        text=UNLINK_MESSAGE_TEXT.format(**formatting),
        html=UNLINK_MESSAGE_HTML.format(**formatting)
    )
    log.debug(f"Notified user of the account unlinking: {user_id}")

    log.debug(f"Finding room hierarchy of the private space...")
    hierarchy = await client.room_hierarchy(MATRIX_PRIVATE_SPACE_ID.__wrapped__, max_depth=9, suggested_only=False)

    log.debug(f"Removing private space leaver from {len(hierarchy)} rooms: {user_id}")
    success_count = 0
    for room in hierarchy:
        room_id = room["room_id"]
        try:
            await client.room_kick(room_id=room_id, user_id=user_id, reason="Left child space")
        except RequestError as e:
            log.warning(f"Could not remove private space leaver {user_id} from {room_id}: {e}")
        else:
            success_count += 1
    log.debug(f"Removed private space leaver from {success_count} rooms: {user_id}")

    log.info(f"Handled leaver of private space: {user_id}")


log.debug(f"Registering client callbacks on: {client}")

# noinspection PyTypeChecker
client.add_event_callback(on_member, nio.InviteMemberEvent)
client.add_event_callback(on_member, nio.RoomMemberEvent)

log.debug(f"Registered client callbacks on: {client}")
