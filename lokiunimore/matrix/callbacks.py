import logging
import nio
from lokiunimore.matrix.client import client
from lokiunimore.matrix.extensions import RequestError
from lokiunimore.config import MATRIX_PARENT_SPACE_ID, MATRIX_CHILD_SPACE_ID, LOKI_BASE_URL
import sqlalchemy.orm
from lokiunimore.sql.engine import engine
from lokiunimore.sql.tables import MatrixUser

log = logging.getLogger(__name__)


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
        # If somebody joins the parent space, notify them of my presence
        if room.room_id == MATRIX_PARENT_SPACE_ID:
            await notify_parent_joiner(event.state_key)
        # If somebody joins the child space, notify them of the successful login
        elif room.room_id == MATRIX_CHILD_SPACE_ID:
            await notify_child_joiner(event.state_key)

    elif event.membership == "leave":
        # If somebody leaves the parent space, remove them from all subrooms, delete their account, and finally notify them
        if room.room_id == MATRIX_PARENT_SPACE_ID:
            await notify_parent_leaver(event.state_key)
        # If somebody leaves the child space, remove them from all subrooms, delete their linking, and finally notify them
        elif room.room_id == MATRIX_CHILD_SPACE_ID:
            await notify_child_leaver(event.state_key)

    elif event.membership == "ban":
        # TODO: If somebody is banned from the parent space... do what?
        pass
        # TODO: If somebody is banned from the child space... do what?
        pass


async def join_when_invited(room: nio.MatrixRoom):
    log.info(f"Received invite to: {room.room_id}")
    await client.join(room.room_id)
    log.info(f"Accepted invite to: {room.room_id}")


WELCOME_MESSAGE_TEXT = """
Benvenuto allo spazio Matrix dell'Unimore!

Sono {username_text}, il bot buttafuori che verifica le credenziali degli utenti che entrano e permette loro di accedere alle rispettive aree.

Se sei uno studente, puoi ottenere accesso all'Area Studenti verificando la tua identità:
{base_url}/matrix/{token}
"""

WELCOME_MESSAGE_HTML = """
<p>
    Benvenuto allo spazio Matrix dell'Unimore!
</p>
<p>
    Sono {username_html}, il bot buttafuori che verifica le credenziali degli utenti che entrano e permette loro di accedere alle rispettive aree.
</p>
<p>
    Se sei uno studente, puoi ottenere accesso all'Area Studenti <a href="{base_url}/matrix/{token}">verificando la tua identità</a>!
</p>
"""


async def notify_parent_joiner(user_id: str):
    log.info(f"User joined parent space: {user_id}")

    log.debug(f"Creating MatrixUser for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user = MatrixUser(id=user_id)
        matrix_user = session.merge(matrix_user)
        session.commit()
        token = matrix_user.token

    log.debug(f"Notifying user of the account creation: {user_id}")

    room_id = await client.pm_slide(user_id)
    display_name = await client.get_displayname(client.user_id)
    formatting = dict(
        username_text=client.user_id,
        username_html=f"""<a href="https://matrix.to/#/{client.user_id}">{display_name}</a>""",
        base_url=LOKI_BASE_URL,
        token=token,
    )
    await client.room_send(room_id, "m.room.message", {
        "msgtype": "m.notice",
        "format": "org.matrix.custom.html",
        "formatted_body": WELCOME_MESSAGE_HTML.format(**formatting),
        "body": WELCOME_MESSAGE_TEXT.format(**formatting),
    })

    log.info(f"Notified joiner of parent space: {user_id}")


async def notify_child_joiner(user_id: str):
    log.info(f"User joined child space: {user_id}")
    # TODO
    log.info(f"Notified joiner of child space: {user_id}")


GOODBYE_MESSAGE_TEXT = """
Hai abbandonato lo spazio Matrix dell'Unimore, quindi ho cancellato i tuoi dati dal mio database; a breve verrai inoltre rimosso da tutte le stanze dello spazio.

Se cambierai idea in futuro, potrai sempre rientrare allo stesso indirizzo!

Abbi un buon proseguimento di giornata! :)
"""

GOODBYE_MESSAGE_HTML = """
<p>
    Hai abbandonato lo spazio Matrix dell'Unimore, quindi ho cancellato i tuoi dati dal mio database; a breve verrai inoltre rimosso da tutte le stanze dello spazio.
</p>
<p>
    Se cambierai idea in futuro, potrai sempre rientrare allo stesso indirizzo!
</p>
<p>
    Abbi un buon proseguimento di giornata! :)
</p>
"""


async def notify_parent_leaver(user_id: str):
    log.info(f"User left parent space: {user_id}")

    log.debug(f"Deleting MatrixUser for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
        if matrix_user is None:
            log.warning(f"User left parent space without a record in the db: {user_id}")
        else:
            if matrix_user.account is not None and len(matrix_user.account.matrix_users) == 1:
                session.delete(matrix_user.account)
            session.delete(matrix_user)
            session.commit()

    room_id = await client.pm_slide(user_id)
    await client.room_send(room_id, "m.room.message", {
        "msgtype": "m.notice",
        "format": "org.matrix.custom.html",
        "formatted_body": GOODBYE_MESSAGE_HTML,
        "body": GOODBYE_MESSAGE_TEXT,
    })

    hierarchy = await client.room_hierarchy(MATRIX_PARENT_SPACE_ID, max_depth=9, suggested_only=False)
    for room in hierarchy:
        room_id = room["room_id"]

        log.debug(f"Removing parent leaver {user_id} from: {room_id}")
        try:
            await client.room_kick(room_id=room_id, user_id=user_id, reason="Left parent space")
        except RequestError as e:
            log.warning(f"Could not remove parent leaver {user_id} from {room_id}: {e}")
        else:
            log.info(f"Removed parent leaver {user_id} from: {room_id}")

    log.info(f"Notified leaver of parent space: {user_id}")


UNLINK_MESSAGE_TEXT = """
Hai abbandonato l'Area Studenti dello spazio Unimore, quindi ho scollegato il tuo account Studenti@Unimore dal tuo account Matrix.

Se cambierai idea in futuro, potrai sempre essere riaggiunto all'Area Studenti ricollegando il tuo account:
{base_url}/matrix/{token}

Abbi un buon proseguimento di giornata! :)
"""

UNLINK_MESSAGE_HTML = """
<p>
    Hai abbandonato l'Area Studenti dello spazio Unimore, quindi ho scollegato il tuo account Studenti@Unimore dal tuo account Matrix.
</p>
<p>
    Se cambierai idea in futuro, potrai sempre essere riaggiunto all'Area Studenti <a href="{base_url}/matrix/{token}">ricollegando il tuo account</a>!
</p>
<p>
    Abbi un buon proseguimento di giornata! :)
</p>
"""


async def notify_child_leaver(user_id: str):
    log.info(f"User left child space: {user_id}")

    log.debug(f"Unlinking MatrixUser for: {user_id}")
    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
        if matrix_user is None:
            log.warning(f"User left child space without a record in the db: {user_id}")
            return
        elif matrix_user.account is None:
            log.warning(f"User left child space without a link in the db: {user_id}")
            token = matrix_user.token
        else:
            if len(matrix_user.account.matrix_users) == 1:
                session.delete(matrix_user.account)
            matrix_user.account = None
            session.commit()
            token = matrix_user.token

    room_id = await client.pm_slide(user_id)
    formatting = dict(
        base_url=LOKI_BASE_URL,
        token=token,
    )
    await client.room_send(room_id, "m.room.message", {
        "msgtype": "m.notice",
        "format": "org.matrix.custom.html",
        "formatted_body": UNLINK_MESSAGE_HTML.format(**formatting),
        "body": UNLINK_MESSAGE_TEXT.format(**formatting),
    })

    hierarchy = await client.room_hierarchy(MATRIX_CHILD_SPACE_ID, max_depth=9, suggested_only=False)
    for room in hierarchy:
        room_id = room["room_id"]

        log.debug(f"Removing child leaver {user_id} from: {room_id}")
        try:
            await client.room_kick(room_id=room_id, user_id=user_id, reason="Left child space")
        except RequestError as e:
            log.warning(f"Could not remove child leaver {user_id} from {room_id}: {e}")
        else:
            log.info(f"Removed child leaver {user_id} from: {room_id}")

    log.info(f"Notified leaver of child space: {user_id}")


# Remember to call this!
def register_callbacks():
    log.debug("Registering callbacks...")
    client.add_event_callback(on_member, nio.InviteMemberEvent)
    client.add_event_callback(on_member, nio.RoomMemberEvent)
    log.debug("Callbacks registered successfully!")
