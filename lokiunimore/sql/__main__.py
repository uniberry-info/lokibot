from lokiunimore.sql.tables import Base
import sqlalchemy
from lokiunimore.config import SQLALCHEMY_DATABASE_URL


sqla_engine: sqlalchemy.engine.Engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL.__wrapped__)
Base.metadata.create_all(bind=sqla_engine)
