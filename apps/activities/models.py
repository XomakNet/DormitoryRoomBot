import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship

from core.db import Base

__author__ = 'Xomak'


class Activity(Base):

    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    do_command = Column(String)
    done_command = Column(String)


class ActivityEvent(Base):

    __tablename__ = 'activities_events'

    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'))
    activity = relationship("Activity")
    compensated_by_id = Column(Integer, ForeignKey('activities_events.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User")
    datetime = Column(DateTime, default=datetime.datetime.now)
    complete_datetime = Column(DateTime)
    assign_type = Column(Enum('move', 'queue'), default='queue')
    status = Column(Enum('pending', 'done', 'absent', 'moved', 'compensated', 'moved_gracefully'))
