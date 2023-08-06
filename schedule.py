import datetime
import enum
import time
from threading import Thread
import abc

import numpy as np
from sqlalchemy import select, func, or_

from models import db_session
from models.db_session import create_session
from models.questions import Question, QuestionAnswer, AnswerState
from models.users import Person, PersonGroup, PersonGroupAssociation
from tools import Settings


class WeekDays(enum.Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class GeneratorInterface(abc.ABC):
    @abc.abstractmethod
    def next_question(self, person: Person) -> Question:
        pass


class SimpleRandomGenerator(GeneratorInterface):
    def next_question(self, person: Person) -> QuestionAnswer:
        with db_session.create_session() as db:
            person_questions = db.scalars(select(Question).
                                          join(Question.groups).
                                          where(PersonGroup.id.in_(pg.id for pg in person.groups)).
                                          group_by(Question.id)).all()

            question = np.random.choice(person_questions)

            cur_answer = QuestionAnswer(question_id=question.id,
                                        person_id=person.id,
                                        ask_time=datetime.datetime.now(),
                                        state=AnswerState.NOT_ANSWERED)

            db.add(cur_answer)
            db.commit()

        return cur_answer


class StatRandomGenerator(GeneratorInterface):
    def next_question(self, person: Person) -> QuestionAnswer:
        with db_session.create_session() as db:
            person_questions = db.scalars(select(Question).
                                          join(Question.groups).
                                          where(PersonGroup.id.in_(pg.id for pg in person.groups)).
                                          group_by(Question.id)).all()

            probabilities = np.zeros(len(person_questions))

            for i, question in enumerate(person_questions):
                question: Question
                correct_count = db.scalar(select(func.count(QuestionAnswer.id)).
                                          join(QuestionAnswer.question).
                                          where(QuestionAnswer.person_id == person.id,
                                                QuestionAnswer.question_id == question.id,
                                                QuestionAnswer.person_answer == Question.answer))

                if correct_count:
                    last_correct_or_ignored = db.scalar(select(QuestionAnswer).
                                                        join(QuestionAnswer.question).
                                                        where(QuestionAnswer.person_id == person.id,
                                                              QuestionAnswer.question_id == question.id,
                                                              or_(QuestionAnswer.person_answer == Question.answer,
                                                                  QuestionAnswer.state != AnswerState.NOT_ANSWERED)).
                                                        order_by(QuestionAnswer.ask_time.desc()))

                    first_answer = db.scalar(select(QuestionAnswer).
                                             where(QuestionAnswer.person_id == person.id,
                                                   QuestionAnswer.question_id == question.id))

                    answers_after_first = db.scalar(select(func.count(QuestionAnswer.id)).
                                                    where(QuestionAnswer.person_id == person.id,
                                                          QuestionAnswer.ask_time > first_answer.ask_time,
                                                          QuestionAnswer.state != AnswerState.NOT_ANSWERED)) + 1

                    max_target_level = db.scalar(select(func.max(PersonGroupAssociation.target_level)).
                                                 where(PersonGroupAssociation.person_id == person.id,
                                                       PersonGroupAssociation.group_id.in_(
                                                           q.id for q in question.groups)))

                    p = (datetime.datetime.now() - last_correct_or_ignored.ask_time).total_seconds() / correct_count
                    p *= np.abs(np.cos(np.pi * np.log2(answers_after_first + 4))) ** (
                            ((answers_after_first + 4) ** 2) / 20)  # planning questions
                    p *= np.e ** (-0.5 * (max_target_level - question.level) ** 2)  # normal by level

                    probabilities[i] = p
                else:
                    probabilities[i] = None

            with_val = list(filter(lambda x: not np.isnan(x), probabilities))
            without_val_count = len(person_questions) - len(with_val)

            increased_avg = (sum(with_val) + without_val_count * max(with_val)) / len(person_questions)

            probabilities[np.isnan(probabilities)] = increased_avg

            probabilities /= sum(probabilities)

            question = np.random.choice(person_questions, p=probabilities)

            cur_answer = QuestionAnswer(question_id=question.id,
                                        person_id=person.id,
                                        ask_time=datetime.datetime.now(),
                                        state=AnswerState.NOT_ANSWERED)

            db.add(cur_answer)
            db.commit()

        return cur_answer


class Schedule(Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self._callback = callback

        self._every = None
        self._order = None  # 1 if time period is calculated first and 0 in other case
        self._week_days = None
        self._from_time = None
        self._to_time = None
        Settings().add_update_handler(self.from_settings)

        self.previous_call = None

        self.generator: GeneratorInterface = StatRandomGenerator()

    def from_settings(self):
        self._every = Settings()['time_period']
        self._order = Settings()['order']
        self._week_days = Settings()['week_days']
        self._from_time = Settings()['from_time']
        self._to_time = Settings()['to_time']

        return self

    def run(self) -> None:
        """The run function of a schedule thread. Note that the order in which you call methods matters.
         on().every() and every().on() play different roles. They in somewhat way mask each-other."""
        while True:
            now = datetime.datetime.now()

            question_for_person = []
            if self._from_time is None or self._from_time <= now.time() <= self._to_time:
                if self.previous_call is None or (now >= self.previous_call + self._every):
                    if self._order == 1:
                        self.previous_call = now
                    if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                        self.task()
                        self.previous_call = now

            time.sleep(1)

    def task(self):
        question_for_person = []
        with db_session.create_session() as db:
            persons = db.scalars(select(Person).where(Person.is_paused == False))
            for person in persons:
                answer = self.generator.next_question(person)
                question_for_person.append((person, answer))

        self._send_to_people(question_for_person)

    def _send_to_people(self, question_to_person):
        with create_session() as db:
            for person, answer in question_to_person:
                if person.is_paused:
                    return

                answer = db.merge(answer)
                person = db.merge(person)

                answer.state = AnswerState.TRANSFERRED
                db.commit()

                self._callback(person, answer)  # Send a question to a person
