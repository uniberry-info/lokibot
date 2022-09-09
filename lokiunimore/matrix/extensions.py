"""
This module defines some extensions for :mod:`nio`, as it is currently missing some methods that :mod:`lokiunimore` desperately needs.
"""
import asyncio
import dataclasses
import pathlib
import json
from typing import Union, Tuple, Any, Optional, TypeVar, Type

T = TypeVar("T")

import aiohttp
import nio
import logging
import hashlib
import hmac

from nio import DataProvider
from nio.crypto import AsyncDataT

log = logging.getLogger(__name__)


@dataclasses.dataclass
class StrippedStateEvent:
    content: dict
    origin_server_ts: int
    sender: str
    state_key: str
    type: str

    @classmethod
    def from_dict(cls, parsed_dict): return cls(**parsed_dict)


@dataclasses.dataclass
class PublicRoomsChunk:
    avatar_url: str
    canonical_alias: str
    children_state: list[StrippedStateEvent]
    guest_can_join: bool
    join_rule: str
    name: str
    num_joined_members: str
    room_id: str
    room_type: str
    topic: str
    world_readable: bool

    @classmethod
    def from_dict(cls, parsed_dict): return cls(**parsed_dict)


@dataclasses.dataclass
class PublicRoomsChunkPartialArray:
    next_batch: str
    rooms: list[PublicRoomsChunk]

    @classmethod
    def from_dict(cls, parsed_dict): return cls(**parsed_dict)


class RequestError(Exception):
    """
    A request to the Matrix homeserver failed.
    """

    def __init__(self, response: nio.responses.ErrorResponse):
        super().__init__()
        self.response: nio.responses.ErrorResponse = response


# noinspection PyProtectedMember
class ExtendedClient(nio.AsyncClient):
    """
    An :class:`~nio.AsyncClient` with some extra features to be upstreamed some day.
    """

    async def register_with_shared_secret(self, shared_secret: str, username: str, displayname: str, password: str):
        """
        Given the homeserver's shared secret, perform a `shared-secret registration <https://matrix-org.github.io/synapse/latest/admin_api/register_api.html#shared-secret-registration>`_.

        :param shared_secret: The shared secret to register with.
        :param username: The username of the user to register.
        :param displayname: The displayname of the user to register.
        :param password: The password of the user to register.
        :raises aiohttp.ClientResponseError: If a request is not successful.
        """

        log.debug(f"Registering {username} with a shared secret...")

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

        log.debug(f"Registered {username} successfully!")

    async def login_with_shared_secret(self, shared_secret: str) -> None:
        """
        Given a shared secret, perform a login via `com.devture.shared_secret_auth <https://github.com/devture/matrix-synapse-shared-secret-auth>`_.

        :param shared_secret: The shared secret to login with.
        """

        log.debug(f"Logging in as {self.user} with a shared secret...")

        token = hmac.new(key=shared_secret.encode("utf8"), msg=self.user.encode("utf8"), digestmod=hashlib.sha512).hexdigest()

        response = await self.login_raw({
            "type": "com.devture.shared_secret_auth",
            "identifier": {
                "type": "m.id.user",
                "user": self.user,
            },
            "token": token,
            "initial_device_display_name": self.device_id,
        })
        if isinstance(response, nio.responses.LoginError):
            breakpoint()
            raise response

        log.debug(f"Login successful!")

    async def get_room_hierarchy(self, room_id: str, max_depth: int, suggested_only: bool) -> list[PublicRoomsChunk]:
        """
        Given a space, get the room hierarchy.

        :param room_id: The id of the space to get the hierarchy of.
        :param max_depth: The max depth of subspaces to recurse into.
        :param suggested_only: Whether only suggested rooms should be returned.
        :return: 
        """

        log.debug(f"Getting room hierarchy for {room_id!r}...")

        current = None
        rooms = []

        while True:
            result: aiohttp.ClientResponse = await self.send(
                "GET",
                nio.Api._build_path(
                    ["rooms", room_id, "hierarchy"],
                    {
                        "max_depth": max_depth,
                        "suggested_only": suggested_only,
                        "from": current
                    }
                )
            )
            result: dict = await result.json()

            rooms = [*rooms, *result["rooms"]]

            current = result.get("next_batch")
            if not current:
                break

        log.debug(f"Successfully retrieved a hierarchy of {len(rooms)} rooms!")

        return rooms

    def dump_state(self, path: pathlib.Path):
        """
        Store important things that aren't already being stored in the :attr:`nio.AsyncClient.store_path` in the given file.

        :param path: The path to store the client state in.
        """
        log.debug(f"Dumping state to {path}...")
        with open(path, "w") as file:
            data = dict()

            data["next_batch"] = self.next_batch
            log.debug(f"Next time, will resume syncing from batch {self.next_batch}")

            json.dump(data, file)

    async def _dump_state_regularly(self, timeout: int):
        """
        Run :meth:`.dump_state` every ``timeout`` seconds.

        :param timeout: The seconds between two calls to ``dump_state``.
        """
        store_path = pathlib.Path(self.store_path)
        state_path = store_path.joinpath("state.json")

        while True:
            await asyncio.sleep(timeout)
            self.dump_state(state_path)

    def load_state(self, path: pathlib.Path):
        """
        Load important things that aren't already being stored in the :attr:`~nio.AsyncClient.store_path` from the given file.

        :param path: The path the client state is stored in.
        """
        log.debug(f"Loading state from {path}...")
        with open(path) as file:
            data = json.load(file)

            self.next_batch = data["next_batch"]
            log.debug(f"Will start syncing from stored batch {self.next_batch}")

    async def sync_forever(self, *args, **kwargs):
        """
        Like :meth:`~nio.AsyncClient.sync_forever`, but with support for all the extensions of :class:`.ExtendedClient`.

        .. seealso:: :meth:`~nio.AsyncClient.sync_forever`
        """

        store_path = pathlib.Path(self.store_path)
        state_path = store_path.joinpath("state.json")
        loop = asyncio.get_event_loop()

        log.debug(f"Ensuring {store_path} exists...")
        store_path.mkdir(parents=True, exist_ok=True)

        try:
            self.load_state(state_path)
        except FileNotFoundError:
            pass

        dump_task = loop.create_task(self._dump_state_regularly(300_000))

        log.debug("Starting to sync...")
        try:
            await super().sync_forever(*args, **kwargs)
        finally:
            log.debug("Stopping to sync...")
            dump_task.cancel("Client stopped syncing.")
            self.dump_state(state_path)

    async def pm_slide(self, user_id: str) -> str:
        """
        Find the first available private message room with the given user, or create one if none exist.

        :param user_id: The user to message.
        :returns: The room id of the created room.
        """

        log.debug(f"Sliding into {user_id}'s PMs...")

        for room in self.rooms.values():
            is_dm = room.tags.get("m.direct")
            is_two_person_group = room.is_group and len(room.users) == 2
            has_user = user_id in room.users.keys()
            if (is_dm or is_two_person_group) and has_user:
                log.debug(f"Found {user_id}'s PM room!")
                return room.room_id
        else:
            log.debug(f"Creating new room for {user_id}'s PMs...")
            response = await self.room_create(invite=[user_id], is_direct=True)
            if isinstance(response, nio.RoomCreateResponse):
                log.debug(f"Room created successfully!")
                return response.room_id
            else:
                raise Exception("Failed to slide into an user's PMs.")

    def _send(
        self,
        response_class: Type[T],
        method: str,
        path: str,
        data: Union[None, str, AsyncDataT] = None,
        response_data: Optional[Tuple[Any, ...]] = None,
        content_type: Optional[str] = None,
        trace_context: Optional[Any] = None,
        data_provider: Optional[DataProvider] = None,
        timeout: Optional[float] = None,
        content_length: Optional[int] = None,
    ) -> T:
        """
        Override :meth:`nio.client.AsyncClient._send` with something that actually raises errors instead of returning them. (Why!?)
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
