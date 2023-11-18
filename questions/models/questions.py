import datetime
import enum
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class AnswerState(enum.Enum):
    NOT_ANSWERED = 0
    TRANSFERRED = 1
    ANSWERED = 2


class QuestionGroupAssociation(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "question_to_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    group_id: Mapped[str] = mapped_column()


class Question(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]
    subject: Mapped[Optional[str]]
    options: Mapped[str]
    answer: Mapped[int]
    groups: Mapped[List[QuestionGroupAssociation]] = relationship()
    level: Mapped[int]
    article_url: Mapped[Optional[str]]


class QuestionAnswer(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    question: Mapped["Question"] = relationship(backref="answers")
    person_id: Mapped[str] = mapped_column()
    person_answer: Mapped[Optional[int]]
    answer_time: Mapped[Optional[datetime.datetime]]
    ask_time: Mapped[datetime.datetime] = mapped_column()
    state: Mapped[AnswerState]

    def __repr__(self):
        return f"<QuestionAnswer(text={self.question_id}, state={self.state}, person_id={self.person_id})>"
