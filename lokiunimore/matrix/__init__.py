import asyncio
import os
import nio
import socket
import logging
from lokiunimore import config

log = logging.getLogger(__name__)


# IDEA ignores the annotations of decorators <https://youtrack.jetbrains.com/issue/PY-53583/Decorator-return-type-ignored>
# noinspection PyTypeChecker
client = nio.AsyncClient(
    homeserver=config.MATRIX_HOMESERVER,
    user=config.MATRIX_USERNAME,
    device_id=f"Loki [Bot] @ {socket.gethostname()}",
)
"""
The bot's Matrix client, powered by :mod:`nio`.
"""


async def get_room_hierarchy(room_id: str):
    # noinspection PyProtectedMember
    await client._send(..., "GET", nio.Api._build_path(["rooms", room_id, "hierarchy"]))


async def on_join_parent_space(user_id: str):
    """
    Callback for when someone joins the monitored "parent" space.
    """

    # TODO: Register on the database
    # TODO: Open private room with them
    # TODO: Send profile link with token


async def on_leave_parent_space(user_id: str):
    """
    Callback for when someone leaves the monitored "parent" space.
    """

    # TODO: Ensure they are not in the child space
    # TODO: Delete from the database


async def on_join_child_space(user_id: str):
    """
    Callback for when someone joins the monitored "child" space.
    """

    # TODO: Verify their registration
    # TODO: If not registered, ban them
    # TODO: Send them welcome message


async def on_leave_child_space(user_id: str):
    """
    Callback for when someone leaves the monitored "child" space.
    """

    # TODO: Unlink account from the database
    # TODO: Send notification message


async def no_op():
    """
    Do nothing, but as a coroutine.
    """
    pass


async def on_join(room: nio.MatrixRoom, event: nio.RoomMemberEvent):
    """
    Callback for when someone joins a room.
    """

    if room.room_id == config.MATRIX_PARENT_SPACE:
        await on_join_parent_space(user_id=event.state_key)

    if room.room_id == config.MATRIX_CHILD_SPACE:
        await on_join_child_space(user_id=event.state_key)


async def on_leave(room: nio.MatrixRoom, event: nio.RoomMemberEvent):
    """
    Callback for when someone leaves a room.
    """

    if room.room_id == config.MATRIX_PARENT_SPACE:
        await on_leave_parent_space(user_id=event.state_key)

    if room.room_id == config.MATRIX_CHILD_SPACE:
        await on_leave_child_space(user_id=event.state_key)


ON_MEMBER_CALLBACKS = {
    "invite": no_op,
    "join": on_join,
    "leave": on_leave,
    "ban": on_leave,  # TODO: handle bans on a space level?
}
"""
Mappings between callbacks and possible :attr:`nio.Event.membership` states.
"""


async def on_member(room: nio.MatrixRoom, event: nio.Event):
    """
    Callback for when a :class:`nio.RoomMemberEvent` is received.
    """

    # Filters allow us to determine the event type in a better way
    event: nio.RoomMemberEvent

    # Delegate to the respective handlers
    await ON_MEMBER_CALLBACKS[event.membership](room, event)


async def on_power(room: nio.MatrixRoom, event: nio.Event):
    """
    Callback for when a :class:`nio.PowerLevelsEvent` is received.
    """

    # Filters allow us to determine the event type in a better way
    event: nio.PowerLevelsEvent

    if room.room_id == config.MATRIX_PARENT_SPACE:
        await on_power_parent_space(event.power_levels)


client.add_event_callback(on_member, nio.RoomMemberEvent)
client.add_event_callback(on_power, nio.PowerLevelsEvent)