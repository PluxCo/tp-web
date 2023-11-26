from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, String


class Message(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "messages"
    tg_id: Mapped[int] = mapped_column(primary_key=True)
    message_ids = Column(String)
    webhook = Column(String)
