from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_CONNECTION_STRING

__author__ = 'Xomak'

engine = create_engine(DATABASE_CONNECTION_STRING)
DbSession = sessionmaker(bind=engine)
Base = declarative_base()


def init_database():
    Base.metadata.create_all(engine)