import sqlalchemy.orm
import logging

log = logging.getLogger(__name__)

from lokiunimore.config import SQLALCHEMY_DATABASE_URL


log.debug(f"Creating SQLAlchemy engine for: {__name__}")
engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL.__wrapped__)
log.debug(f"Created SQLAlchemy engine for: {__name__}")


__all__ = (
    "engine",
)
