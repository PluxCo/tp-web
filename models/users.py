from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, ARRAY, Table
from sqlalchemy.orm import relationship, mapped_column

from .db_session import SqlAlchemyBase


class PersonGroupAssociation(SqlAlchemyBase):
    __tablename__ = "person_to_group"

    person_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, primary_key=True)


class PersonGroup(SqlAlchemyBase):
    __tablename__ = "person_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)


class Person(SqlAlchemyBase):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String)
    groups = relationship("PersonGroup", secondary="person_to_group")
    level = Column(Integer)
    tg_id = Column(Integer, unique=True)
