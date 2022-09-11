import nio
import logging
import sqlalchemy.orm
import functools

log = logging.getLogger(__name__)

from lokiunimore.config import MATRIX_SKIP_EVENTS
from lokiunimore.matrix.database import engine
from lokiunimore.sql.tables import MatrixProcessedEvent


def filter_processed_events(f):
    """
    Decorator applicable to a :mod:`nio` callback to filter incoming events whose IDs have been marked in the database as *already processed*, and marking events successfully processed by the function as "processed".
    """

    @functools.wraps(f)
    async def wrapped(room: nio.MatrixRoom, event: nio.Event):
        log.debug(f"Checking if event should be processed: {event.event_id}")
        if should_process_event(event):
            if not MATRIX_SKIP_EVENTS.__wrapped__:
                log.debug(f"Processing event: {event.event_id}")
                await f(room, event)
            else:
                log.debug(f"Skipping event due to MATRIX_SKIP_EVENTS: {event.event_id}")
            log.debug(f"Marking event as processed: {event.event_id}")
            mark_event_as_processed(event)
        else:
            log.debug(f"Skipping already processed event: {event.event_id}")

    return wrapped


def should_process_event(event: nio.Event) -> bool:
    """
    Check if the event should be processed.

    :param event: The event to check.
    :return: :data:`True` if the event should be processed, :data:`False` otherwise.
    """

    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        return session.query(MatrixProcessedEvent).get(event.event_id) is None


def mark_event_as_processed(event: nio.Event):
    """
    Mark the event as processed, preventing it from being processed again.

    :param event: The event to mark.
    :return: The created and committed :class:`lokiunimore.sql.tables.MatrixProcessedEvent` instance.
    """

    with sqlalchemy.orm.Session(bind=engine) as session:
        session: sqlalchemy.orm.Session
        mpe = MatrixProcessedEvent(id=event.event_id)
        session.add(mpe)
        session.commit()
        return mpe


__all__ = (
    "filter_processed_events",
)
