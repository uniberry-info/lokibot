import sqlalchemy.engine
from lokiunimore.config import SQLALCHEMY_DATABASE_URL


engine = sqlalchemy.engine.create_engine(SQLALCHEMY_DATABASE_URL.__wrapped__)


__all__ = (
    "engine",
)