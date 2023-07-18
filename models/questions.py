import enum

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Time, Enum
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase
from .users import PersonGroup, Person


class AnswerState(enum.Enum):
    NOT_ANSWERED = 0
    TRANSFERRED = 1
    ANSWERED = 2


class Question(SqlAlchemyBase):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text)
    options = Column(Text)
    answer = Column(Integer)
    group_id = Column(ForeignKey("person_groups.id"))
    group = relationship("PersonGroup")
    level = Column(Integer)
    article_url = Column(String)


class QuestionAnswer(SqlAlchemyBase):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(ForeignKey("questions.id"))
    question = relationship("Question")
    person_id = Column(ForeignKey("persons.id"))
    person = relationship("Person")
    answered_time = Column(Time)
    ask_time = Column(Time)
    state = Column(Enum(AnswerState))
