import nio
import logging
from lokiunimore import config
from lokiunimore.utils import no_op
from lokiunimore.matrix.extensions import ExtendedClient

log = logging.getLogger(__name__)


# IDEA ignores the annotations of decorators <https://youtrack.jetbrains.com/issue/PY-53583/Decorator-return-type-ignored>
# noinspection PyTypeChecker
client = ExtendedClient(
    homeserver=config.MATRIX_HOMESERVER.__wrapped__,
    user=config.MATRIX_USERNAME.__wrapped__,
)
"""
The bot's Matrix client, powered by :mod:`nio`.
"""


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

    # TODO: Determine the rooms where the change should be applied in
    # TODO: Ensure they are not in the child space
    # TODO: Delete from the database


async def on_ban_parent_space(user_id: str):
    """
    Callback for when someone is banned from the monitored "parent" space.
    """

    # TODO: Determine the rooms where the change should be applied in
    # TODO: Propagate the ban downwards
    # TODO: Delete from the database


async def on_power_parent_space(power: nio.PowerLevels):
    """
    Callback for when the power levels of the monitored "parent" space are changed.
    """

    # TODO: Determine the rooms where the change should be applied in
    # TODO: Propagate the change downwards


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

    # TODO: Determine the rooms where the change should be applied in
    # TODO: Ensure they are not in the child space
    # TODO: Unlink account from the database
    # TODO: Send notification message


async def on_join(room: nio.MatrixRoom, event: nio.RoomMemberEvent):
    """
    Callback for when someone joins a room.
    """

    if room.room_id == config.MATRIX_PARENT_SPACE_ID:
        await on_join_parent_space(user_id=event.state_key)

    if room.room_id == config.MATRIX_CHILD_SPACE_ID:
        await on_join_child_space(user_id=event.state_key)


async def on_leave(room: nio.MatrixRoom, event: nio.RoomMemberEvent):
    """
    Callback for when someone leaves a room.
    """

    if room.room_id == config.MATRIX_PARENT_SPACE_ID:
        await on_leave_parent_space(user_id=event.state_key)

    if room.room_id == config.MATRIX_CHILD_SPACE_ID:
        await on_leave_child_space(user_id=event.state_key)


async def on_ban(room: nio.MatrixRoom, event: nio.RoomMemberEvent):
    """
    Callback for when someone is banned from a room.
    """

    if room.room_id == config.MATRIX_PARENT_SPACE_ID:
        await on_ban_parent_space(user_id=event.state_key)


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

    if room.room_id == config.MATRIX_PARENT_SPACE_ID:
        await on_power_parent_space(event.power_levels)


client.add_event_callback(on_member, nio.RoomMemberEvent)
client.add_event_callback(on_power, nio.PowerLevelsEvent)
