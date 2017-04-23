from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from core.db import Base

__author__ = 'Xomak'


class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    name = Column(String)
    is_admin = Column(Boolean)