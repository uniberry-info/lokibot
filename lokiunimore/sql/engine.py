import sqlalchemy.orm
from lokiunimore.config import SQLALCHEMY_DATABASE_URI


engine = sqlalchemy.create_engine(url=SQLALCHEMY_DATABASE_URI.__wrapped__)
