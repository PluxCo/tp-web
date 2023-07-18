from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, ARRAY
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class PersonGroup(SqlAlchemyBase):
    __tablename__ = "person_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)


class Person(SqlAlchemyBase):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String)
    group_id = Column(ForeignKey("person_groups.id"))
    group = relationship("PersonGroup")
    level = Column(Integer)
    tg_id = Column(Integer, unique=True)
