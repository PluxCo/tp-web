from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, String,Integer


class Message(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer)
    message_id = Column(String)
    webhook = Column(String)
