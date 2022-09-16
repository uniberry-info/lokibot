"""
This module defines some extensions for :mod:`nio`, as it is currently missing some methods that :mod:`lokiunimore` desperately needs.

It also defines a custom client with the functions we need to run :mod:`lokiunimore`.
"""
import contextlib

import aiohttp
import nio
import nio.crypto
import logging
import hashlib
import hmac
import typing as t
import functools
import sqlalchemy
import sqlalchemy.orm
import flask

T = t.TypeVar("T")
log = logging.getLogger(__name__)

from lokiunimore.sql.tables import MatrixUser, MatrixProcessedEvent
from lokiunimore.utils.device_names import generate_device_name
from lokiunimore.config import MATRIX_PUBLIC_SPACE_ID, MATRIX_PRIVATE_SPACE_ID, MATRIX_SKIP_EVENTS
from lokiunimore.matrix.templates.messages import WELCOME_MESSAGE_TEXT, WELCOME_MESSAGE_HTML, SUCCESS_MESSAGE_TEXT, SUCCESS_MESSAGE_HTML, GOODBYE_MESSAGE_TEXT, GOODBYE_MESSAGE_HTML, UNLINK_MESSAGE_TEXT, UNLINK_MESSAGE_HTML
from lokiunimore.web.app import app


class RequestError(Exception):
    """
    A request to the Matrix homeserver failed.
    """

    def __init__(self, response: nio.responses.ErrorResponse):
        super().__init__()
        self.response: nio.responses.ErrorResponse = response


# noinspection PyProtectedMember
class ExtendedAsyncClient(nio.AsyncClient):
    """
    An :class:`~nio.AsyncClient` with some extra features to be upstreamed some day.
    """

    def __repr__(self):
        return f"<{self.__class__.__qualname__} for {self.user} at {self.homeserver}>"

    def _send(
            self,
            response_class: t.Type[T],
            method: str,
            path: str,
            data: t.Union[None, str, nio.crypto.AsyncDataT] = None,
            response_data: t.Optional[t.Tuple[t.Any, ...]] = None,
            content_type: t.Optional[str] = None,
            trace_context: t.Optional[t.Any] = None,
            data_provider: t.Optional[nio.DataProvider] = None,
            timeout: t.Optional[float] = None,
            content_length: t.Optional[int] = None,
    ) -> T:
        """
        Override :meth:`nio.client.AsyncClient._send` with something that actually raises errors instead of returning them.

        .. danger::

            SUPER UNTESTED. PLEASE WORK. PLEASE DO. PLEASE DO NOT EXPLODE IN PRODUCTION.
        """
        result = super()._send(
            response_class=response_class,
            method=method,
            path=path,
            data=data,
            response_data=response_data,
            content_type=content_type,
            trace_context=trace_context,
            data_provider=data_provider,
            timeout=timeout,
            content_length=content_length,
        )

        if isinstance(result, nio.responses.ErrorResponse):
            log.warning(f"{method} {path} errored: {result!r}")
            raise RequestError(result)

        return result

    async def register_with_shared_secret(self, shared_secret: str, username: str, displayname: str, password: str):
        """
        Given the homeserver's shared secret, perform a `shared-secret registration <https://matrix-org.github.io/synapse/latest/admin_api/register_api.html#shared-secret-registration>`_.

        :param shared_secret: The shared secret to register with.
        :param username: The username of the user to register.
        :param displayname: The displayname of the user to register.
        :param password: The password of the user to register.
        :raises aiohttp.ClientResponseError: If a request is not successful.

        .. note:: ``shared_secret`` is not the same shared secret of :meth:`.login_with_shared_secret`.
        """

        log.debug(f"Registering via shared-secret registration: {username}")

        path = nio.Api._build_path(
            ["v1", "register"],
            base_path="/_synapse/admin"
        )

        nonce: aiohttp.ClientResponse = await self.send("GET", path)
        nonce.raise_for_status()
        nonce: dict[str, ...] = await nonce.json()
        nonce: str = nonce["nonce"]

        mac = hmac.new(shared_secret.encode("utf8"), digestmod=hashlib.sha1)
        mac.update(nonce.encode("utf8"))
        mac.update(b"\0")
        mac.update(username.encode("utf8"))
        mac.update(b"\0")
        mac.update(password.encode("utf8"))
        mac.update(b"\0")
        mac.update(b"notadmin")

        registration: aiohttp.ClientResponse = await self.send("POST", path, nio.Api.to_json({
            "nonce": nonce,
            "username": username,
            "displayname": displayname,
            "password": password,
            "admin": False,
            "mac": mac.hexdigest()
        }))
        registration.raise_for_status()

        log.info(f"Registered via shared-secret registration: {username}")

    async def login_with_shared_secret(self, shared_secret: str) -> None:
        """
        Given a shared secret, perform a login via `com.devture.shared_secret_auth <https://github.com/devture/matrix-synapse-shared-secret-auth>`_.

        :param shared_secret: The shared secret to login with.

        .. note:: ``shared_secret`` is not the same shared secret of :meth:`.register_with_shared_secret`.
        """

        log.debug(f"Logging in as {self.user} with a shared secret...")

        token = hmac.new(key=shared_secret.encode("utf8"), msg=self.user.encode("utf8"), digestmod=hashlib.sha512).hexdigest()

        await self.login_raw({
            "type": "com.devture.shared_secret_auth",
            "identifier": {
                "type": "m.id.user",
                "user": self.user,
            },
            "token": token,
            "initial_device_display_name": generate_device_name(__name__),
        })

        log.debug(f"Login successful!")

    async def room_hierarchy(self, room_id: str, max_depth: int, suggested_only: bool) -> list[dict]:
        """
        Given a space, get the room hierarchy.

        :param room_id: The id of the space to get the hierarchy of.
        :param max_depth: The max depth of subspaces to recurse into.
        :param suggested_only: Whether only suggested rooms should be returned.
        :return:
        """

        log.debug(f"Getting room hierarchy for: {room_id!r}")

        current = None
        rooms = []

        while True:
            path = ["rooms", room_id, "hierarchy"]
            query = {
                "max_depth": str(max_depth),
                "suggested_only": str(suggested_only).lower(),
            }
            if current:
                query["from"] = current

            result: aiohttp.ClientResponse = await self.send(
                "GET",
                nio.Api._build_path(path, query, base_path="/_matrix/client/v1"),
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )
            result: dict = await result.json()

            rooms = [*rooms, *result["rooms"]]

            current = result.get("next_batch")
            if not current:
                break

        log.debug(f"Successfully retrieved a hierarchy of {len(rooms)} rooms!")

        return rooms

    async def find_or_create_pm_room(self, user_id: str) -> str:
        """
        Find the first available private message room with the given user, or create one if none exist.

        :param user_id: The user to message.
        :returns: The room id of the created room.
        """

        log.debug(f"Sliding into {user_id}'s PMs...")

        for room in self.rooms.values():
            is_dm = "m.direct" in room.tags
            is_group = room.is_group
            has_two_users = len(room.users) + len(room.invited_users) == 2
            contains_user_id = user_id in room.users.keys() or user_id in room.invited_users.keys()

            if (is_dm or is_group) and has_two_users and contains_user_id:
                log.debug(f"Found PM room for: {user_id}")
                return room.room_id
        else:
            log.debug(f"Creating new PM room for: {user_id}")
            response = await self.room_create(invite=[user_id], is_direct=True)
            if isinstance(response, nio.RoomCreateResponse):
                log.info(f"Created new PM room for: {user_id}")
                return response.room_id
            else:
                raise Exception("Failed to slide into an user's PMs.")

    async def room_send_message_html(self, room_id: str, text: str, html: str):
        """
        Send an HTML message with a text fallback.

        :param room_id: The ID of the room to send the message in.
        :param text: The plain text fallback of the message.
        :param html: The HTML message.
        :return: I have no idea, whatever :meth:`~nio.client.AsyncClient.room_send` does.
        """

        return await self.room_send(room_id, "m.room.message", {
            "msgtype": "m.notice",
            "format": "org.matrix.custom.html",
            "formatted_body": html,
            "body": text,
        })

    async def mention_html(self, user_id: str) -> str:
        """
        Create a rich HTML mention.

        To provide a text fallback for the HTML mention, use the ``user_id``.

        :param user_id: The user to mention.
        :return: The HTML string.
        """

        display_name = await self.get_displayname(user_id)

        # language=html
        return f"""<a href="https://matrix.to/#/{user_id}">{display_name}</a>"""


def filter_processed_events(f):
    """
    Decorator applicable to a :mod:`nio` callback to filter incoming events whose IDs have been marked in the database as *already processed*, and marking events successfully processed by the function as "processed".
    """

    @functools.wraps(f)
    async def wrapped(self, room: nio.MatrixRoom, event: nio.Event):
        if event_id := getattr(event, "event_id", None):
            log.debug(f"Checking if event should be processed: {event_id}")
            if self._event_processed_check(event):
                if not MATRIX_SKIP_EVENTS.__wrapped__:
                    log.debug(f"Processing event: {event_id}")
                    await f(self, room, event)
                else:
                    log.debug(f"Skipping event due to MATRIX_SKIP_EVENTS: {event_id}")
                log.debug(f"Marking event as processed: {event_id}")
                self._event_processed_mark(event)
            else:
                log.debug(f"Skipping already processed event: {event_id}")
        else:
            log.debug(f"Received partial event with no id, which should always be processed")
            await f(self, room, event)
            log.debug(f"Processed partial event successfully")

    return wrapped


class LokiClient(ExtendedAsyncClient):
    def __init__(self, *args, database_url: str, **kwargs):
        super().__init__(*args, **kwargs)

        self.sqla_engine: sqlalchemy.engine.Engine = sqlalchemy.create_engine(database_url)
        """
        The :mod:`sqlalchemy` :class:`~sqlalchemy.engine.Engine` associated with this client.
        """

        # noinspection PyTypeChecker
        self.add_event_callback(self.__handle_membership_change, nio.InviteMemberEvent)
        # noinspection PyTypeChecker
        self.add_event_callback(self.__handle_membership_change, nio.RoomMemberEvent)

    @contextlib.contextmanager
    def _sqla_session(self) -> t.Generator[sqlalchemy.orm.Session, None, None]:
        """
        Open a new :mod:`sqlalchemy` :class:`~sqlalchemy.orm.Session` using this object's :attr:`.sql_engine` via a context manager interface.
        """

        with sqlalchemy.orm.Session(bind=self.sqla_engine) as session:
            yield session

    def _event_processed_check(self, event: nio.Event) -> bool:
        """
        Check if a received event should be processed.

        :param event: The event to check.
        :return: :data:`True` if the event should be processed, :data:`False` otherwise.
        """

        with self._sqla_session() as session:
            session: sqlalchemy.orm.Session
            return session.query(MatrixProcessedEvent).get(event.event_id) is None

    def _event_processed_mark(self, event: nio.Event):
        """
        Mark the event as processed, preventing it from being processed again.

        :param event: The event to mark.
        :return: The created and committed :class:`lokiunimore.sql.tables.MatrixProcessedEvent` instance.
        """

        with self._sqla_session() as session:
            session: sqlalchemy.orm.Session
            mpe: MatrixProcessedEvent = MatrixProcessedEvent(id=event.event_id)
            session.add(mpe)
            session.commit()
            return mpe

    @staticmethod
    def _loki_web_profile(token: str):
        with app.app_context():
            return flask.url_for("page_matrix_profile", token=token)

    @filter_processed_events
    async def __handle_membership_change(self, room: nio.MatrixRoom, event: nio.Event) -> None:
        # Filters allow us to determine the event type in a better way
        event: nio.InviteMemberEvent | nio.RoomMemberEvent

        # Catch events about myself immediately
        if event.state_key == self.user_id:
            # If I'm invited to a room, join it
            if event.membership == "invite":
                await self.__handle_received_invite(room)

        elif event.membership == "join":
            # If somebody joins the parent space, notify them of my presence and send them their profile URL
            if room.room_id == MATRIX_PUBLIC_SPACE_ID:
                await self.__handle_public_space_joiner(event.state_key)
            # If somebody joins the child space, notify them of the successful login
            elif room.room_id == MATRIX_PRIVATE_SPACE_ID:
                await self.__handle_private_space_joiner(event.state_key)

        elif event.membership == "leave":
            # If somebody leaves the parent space, remove them from all subrooms, delete their account, and finally notify them
            if room.room_id == MATRIX_PUBLIC_SPACE_ID:
                await self.__handle_public_space_leaver(event.state_key)
            # If somebody leaves the child space, remove them from all subrooms, delete their linking, and finally notify them
            elif room.room_id == MATRIX_PRIVATE_SPACE_ID:
                await self.__handle_private_space_leaver(event.state_key)

        elif event.membership == "ban":
            # TODO: If somebody is banned from the parent space... propagate the ban?
            if room.room_id == MATRIX_PUBLIC_SPACE_ID:
                await self.__handle_public_space_leaver(event.state_key)
            # TODO: If somebody is banned from the child space... propagate the ban?
            elif room.room_id == MATRIX_PRIVATE_SPACE_ID:
                await self.__handle_private_space_leaver(event.state_key)

    async def __handle_received_invite(self, room: nio.MatrixRoom):
        log.debug(f"Received invite to: {room.room_id}")
        await self.join(room.room_id)
        log.info(f"Accepted invite to: {room.room_id}")

    async def __handle_public_space_joiner(self, user_id: str):
        log.debug(f"User joined public space: {user_id}")

        log.debug(f"Creating MatrixUser for: {user_id}")
        with self._sqla_session() as session:
            session: sqlalchemy.orm.Session
            matrix_user = MatrixUser(id=user_id)
            matrix_user = session.merge(matrix_user)
            session.commit()
            log.debug(f"Created MatrixUser for: {user_id}")
            token = matrix_user.token

        log.debug(f"Notifying user of the account creation: {user_id}")
        formatting = dict(
            username_text=self.user_id,
            username_html=await self.mention_html(self.user_id),
            profile_url=self._loki_web_profile(token),
        )
        await self.room_send_message_html(
            await self.find_or_create_pm_room(user_id),
            text=WELCOME_MESSAGE_TEXT.format(**formatting),
            html=WELCOME_MESSAGE_HTML.format(**formatting)
        )
        log.debug(f"Notified user of the account creation: {user_id}")

        log.info(f"Handled joiner of public space: {user_id}")

    async def __handle_private_space_joiner(self, user_id: str):
        log.info(f"User joined private space: {user_id}")

        log.debug(f"Setting MatrixUser as joined for: {user_id}")
        with self._sqla_session() as session:
            session: sqlalchemy.orm.Session
            matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
            matrix_user.joined_private_space = True
            session.commit()
            log.debug(f"Set MatrixUser as joined for: {user_id}")
            token = matrix_user.token

        log.debug(f"Notifying user of the account link: {user_id}")
        formatting = dict(
            profile_url=self._loki_web_profile(token),
        )
        await self.room_send_message_html(
            await self.find_or_create_pm_room(user_id),
            text=SUCCESS_MESSAGE_TEXT.format(**formatting),
            html=SUCCESS_MESSAGE_HTML.format(**formatting)
        )
        log.debug(f"Notified user of the account link: {user_id}")

        log.info(f"Handled joiner of private space: {user_id}")

    async def __handle_public_space_leaver(self, user_id: str):
        log.info(f"User left public space: {user_id}")

        log.debug(f"Deleting MatrixUser for: {user_id}")
        with self._sqla_session() as session:
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
        await self.room_send_message_html(
            await self.find_or_create_pm_room(user_id),
            text=GOODBYE_MESSAGE_TEXT,
            html=GOODBYE_MESSAGE_HTML
        )
        log.debug(f"Notified user of the account deletion: {user_id}")

        log.debug(f"Finding room hierarchy of the public space...")
        public_hierarchy = await self.room_hierarchy(MATRIX_PUBLIC_SPACE_ID.__wrapped__, max_depth=9, suggested_only=False)

        log.debug(f"Finding room hierarchy of the private space...")
        private_hierarchy = await self.room_hierarchy(MATRIX_PRIVATE_SPACE_ID.__wrapped__, max_depth=9, suggested_only=False)

        hierarchy = [*public_hierarchy, *private_hierarchy]

        log.debug(f"Removing public space leaver from {len(hierarchy)} rooms: {user_id}")
        success_count = 0
        for room in hierarchy:
            room_id = room["room_id"]
            try:
                await self.room_kick(room_id=room_id, user_id=user_id, reason="Loki account deleted")
            except RequestError as e:
                log.warning(f"Could not remove public space leaver {user_id} from {room_id}: {e!r}")
            else:
                success_count += 1
        log.debug(f"Removed public space leaver from {success_count} rooms: {user_id}")

        log.info(f"Handled leaver of public space: {user_id}")

    async def __handle_private_space_leaver(self, user_id: str):
        log.debug(f"User left private space: {user_id}")

        log.debug(f"Unlinking account for: {user_id}")
        with self._sqla_session() as session:
            session: sqlalchemy.orm.Session
            matrix_user: MatrixUser = session.query(MatrixUser).get(user_id)
            if matrix_user is None:
                log.warning(f"User left private space without having a pre-existent record in the db: {user_id}")
                return
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
            profile_url=self._loki_web_profile(token),
        )
        await self.room_send_message_html(
            await self.find_or_create_pm_room(user_id),
            text=UNLINK_MESSAGE_TEXT.format(**formatting),
            html=UNLINK_MESSAGE_HTML.format(**formatting)
        )
        log.debug(f"Notified user of the account unlinking: {user_id}")

        log.debug(f"Finding room hierarchy of the private space...")
        hierarchy = await self.room_hierarchy(MATRIX_PRIVATE_SPACE_ID.__wrapped__, max_depth=9, suggested_only=False)

        log.debug(f"Removing private space leaver from {len(hierarchy)} rooms: {user_id}")
        success_count = 0
        for room in hierarchy:
            room_id = room["room_id"]
            try:
                await self.room_kick(room_id=room_id, user_id=user_id, reason="Loki account unlinked")
            except RequestError as e:
                log.warning(f"Could not remove private space leaver {user_id} from {room_id}: {e}")
            else:
                success_count += 1
        log.debug(f"Removed private space leaver from {success_count} rooms: {user_id}")

        log.info(f"Handled leaver of private space: {user_id}")
