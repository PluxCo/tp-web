import datetime
import enum
import json
import math
import string
import time
from collections import defaultdict
from threading import Thread, Timer

import numpy as np
from faker import Faker
from sqlalchemy import select, and_

from models import questions, users
from models.db_session import Session, create_session
from tools import Settings


def fake_db(session: Session, scale=None):
    if scale is None:
        scale = [4, 8, 16, 32]
    fake = Faker('ru_RU')
    db = session
    group_list = []
    question_list = []
    person_list = []

    for i in range(0, scale[0]):
        group = users.PersonGroup()
        group.name = fake.word()
        group_list.append(group)
        db.add(group)
    db.commit()

    for i in range(0, scale[1]):
        person = users.Person()
        person.full_name = fake.name()
        person.tg_id = fake.random_int(min=1_000_000, max=1_000_000_000)
        person.level = fake.random_int(min=1, max=5)
        person.groups.append(fake.random_element(elements=group_list))
        person_list.append(person)
        db.add(person)
    db.commit()

    for i in range(0, scale[2]):
        question = questions.Question()
        question.text = fake.sentence()

        options = [fake.sentence(), fake.sentence(), fake.sentence(), fake.sentence()]
        question.options = json.dumps(options, ensure_ascii=False)
        question.answer = np.random.randint(1, 5)

        question.level = fake.random_int(min=1, max=5)
        question.article_url = fake.url()
        question.groups.append(fake.random_element(elements=group_list))
        question.subject = fake.word()

        question_list.append(question)
        db.add(question)
    db.commit()

    for i in range(0, scale[3]):
        answer = questions.QuestionAnswer()
        answer.question = fake.random_element(elements=question_list)
        answer.question_id = answer.question.id

        answer.person = fake.random_element(elements=person_list)
        answer.person_id = answer.person.id

        answer.answer_time = fake.date_time_this_year()
        answer.ask_time = answer.answer_time

        answer.person_answer = np.random.randint(1, 5)
        answer.state = questions.AnswerState.ANSWERED

        db.add(answer)
    db.commit()


class WeekDays(enum.Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class Schedule(Thread):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._every = None
        self._order = None  # 1 if time period is calculated first and 0 in other case
        self._week_days = None
        self._distribution_function = None
        self._repetition_amount = None
        self._from_time = None
        self._to_time = None

    def every(self, seconds: float = 0, minutes: float = 0, hours: float = 0,
              days: float = 0, weeks: float = 0):
        self._every = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)

        if self._order is None:
            self._order = 1

        return self

    def on(self, dt: list[WeekDays] or WeekDays):
        if type(dt) == list:
            self._week_days = [WeekDays(x) for x in dt]
        else:
            self._week_days = [WeekDays(dt)]
        if self._order is None:
            self._order = 0

        return self

    def using_repetition_function(self, distribution_function=math.exp, repetition_amount=6):
        self._distribution_function = distribution_function
        self._repetition_amount = repetition_amount

        return self

    def from_settings(self):
        self._every = Settings()['time_period']
        self._order = Settings()['order']
        self._week_days = Settings()['week_days']
        self._distribution_function = Settings()['distribution_function']
        self._repetition_amount = Settings()['repetition_amount']
        self._from_time = Settings()['from_time']
        self._to_time = Settings()['to_time']

        return self

    def run(self) -> None:
        """The run function of a schedule thread. Note that the order in which you call methods matters.
         on().every() and every().on() play different roles. They in somewhat way mask each-other."""
        db = create_session()
        previous_call = None
        while True:
            persons = db.scalars(select(users.Person)).all()
            question_for_person = {}
            now = datetime.datetime.now()
            if self._repetition_amount is not None:
                for person in persons:
                    questions_to_ask_now = self._plan_questions(person.id, now)
                    if len(questions_to_ask_now) != 0:
                        question_for_person[person.id] = np.random.choice(questions_to_ask_now)
                    else:
                        question_for_person[person.id] = self._random_question(person.id)
                previous_call = self._periodic_call(now, previous_call, question_for_person)
            else:
                for person in persons:
                    question_for_person[person.id] = self._random_question(person.id)
                previous_call = self._periodic_call(now, previous_call, question_for_person)
            time.sleep(1)

    def _random_question(self, person_id: int, group_id: list or int = None) -> int:
        """Gives random question id within the same group, which hasn't been asked yet if such question exists
        """

        with create_session() as db:
            person = db.scalar(select(users.Person).where(users.Person.id == person_id))
            search_window = datetime.timedelta(self._distribution_function(self._repetition_amount))

            if group_id is None:
                groups = [x.id for x in person.groups]
            elif group_id is int:
                groups = [group_id]
            else:
                groups = group_id
            groups: list

            question_ids = [x.id for x in db.scalars(
                select(questions.Question).join(questions.Question.groups).where(users.PersonGroup.id.in_(groups)))]
            answered_question_ids = [x.question_id for x in db.scalars(
                select(questions.QuestionAnswer).where(questions.QuestionAnswer.person_id == person_id).where(
                    questions.QuestionAnswer.ask_time > datetime.datetime.now() - search_window))]

            result_list = list(set(question_ids).difference(answered_question_ids))
            if len(result_list) > 0:
                return np.random.choice(result_list)
            else:
                return np.random.choice(question_ids)

    def _plan_questions(self, person_id: int, now=datetime.datetime.now()):
        tic = time.perf_counter()
        db = create_session()
        answers_map = defaultdict(list)
        questions_to_ask = []

        answered_questions = db.scalars(
            select(questions.QuestionAnswer).where(and_(questions.QuestionAnswer.person_id == person_id,
                                                        questions.QuestionAnswer.state == questions.AnswerState.ANSWERED)).order_by(
                questions.QuestionAnswer.ask_time.desc())).all()

        planned_questions = db.scalars(
            select(questions.QuestionAnswer).where(questions.QuestionAnswer.person_id == person_id).where(
                questions.QuestionAnswer.state == questions.AnswerState.NOT_ANSWERED).order_by(
                questions.QuestionAnswer.ask_time.desc())).all()

        transferred_questions = db.scalars(
            select(questions.QuestionAnswer).where(questions.QuestionAnswer.person_id == person_id).where(
                questions.QuestionAnswer.state == questions.AnswerState.TRANSFERRED).order_by(
                questions.QuestionAnswer.ask_time.desc())).all()

        for answer in planned_questions:  # Add questions which were planned to ask before to the list
            questions_to_ask.append(answer.question_id)

        for answer in answered_questions:  # Add questions which were not planned yet to the map of questions for repeat
            if answer.question_id not in questions_to_ask:
                answers_map[answer.question_id].append(answer)

        for answer in transferred_questions:  # Add questions which were transferred to the database as planed
            if answer.question_id not in questions_to_ask:
                answer.state = questions.AnswerState.ANSWERED

                planned_answer = questions.QuestionAnswer()
                planned_answer.ask_time = now + self._every
                planned_answer.state = questions.AnswerState.NOT_ANSWERED
                planned_answer.question_id = answer.question_id
                planned_answer.person_id = person_id
                db.add(planned_answer)

        for key in answers_map:  # Add questions which require repetition to the database as planed
            length = len(answers_map[key])
            if length < self._repetition_amount:
                delta = datetime.timedelta(self._distribution_function(length))
                planned_answer = questions.QuestionAnswer()
                planned_answer.ask_time = delta + answers_map[key][0].ask_time
                planned_answer.state = questions.AnswerState.NOT_ANSWERED
                planned_answer.question_id = key
                planned_answer.person_id = person_id
                db.add(planned_answer)

        db.commit()
        return questions_to_ask

    def _periodic_call(self, now, previous_call, args):
        if self._from_time is None or self._from_time <= now.time() <= self._to_time:
            if self._order == 1:
                if previous_call is None or (now >= previous_call + self._every):
                    previous_call = now
                    if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                        self._send_to_people(args, now)
                        previous_call = now
            if self._order == 0:
                if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                    if previous_call is None or (now >= previous_call + self._every):
                        self._send_to_people(args, now)
                        previous_call = now

        return previous_call

    def _send_to_people(self, question_to_person, now):
        with create_session() as db:
            for person_id in question_to_person:
                question_id = int(question_to_person[person_id])
                person_id: int

                question = db.get(questions.Question, int(question_id))
                person = db.get(users.Person, person_id)
                self._callback(person, question)

                # TODO: Move the lines bellow to check_answer in bot.py
                #
                # with db_session.create_session() as db:
                #     question_id = question[call.from_user.id].id
                #     person_answer = int(call.data.split('_')[1])
                #     person_id = db.scalar(select(users.Person).where(users.Person.tg_id == call.from_user.id)).id
                #     planned_question = db.scalar(select(questions.QuestionAnswer).where(
                #         questions.QuestionAnswer.person_id == person_id).where(
                #         questions.QuestionAnswer.question_id == question_id).where(
                #         questions.QuestionAnswer.state == questions.AnswerState.NOT_ANSWERED))
                #     if planned_question is not None:
                #         planned_question.person_answer = person_answer
                #         planned_question.state = questions.AnswerState.ANSWERED if person_answer == question[
                #             call.from_user.id].answer else \
                #             questions.AnswerState.TRANSFERRED
                #         planned_question.answer_time = datetime.datetime.now()
                #         db.commit()
                #     else:
                #         planned_question = questions.QuestionAnswer()
                #         planned_question.answer_time = datetime.datetime.now()
                #         planned_question.ask_time = planned_question.answer_time
                #         planned_question.question_id = question_id
                #         planned_question.person_answer = person_answer
                #         planned_question.person_id = person_id
                #         planned_question.state = questions.AnswerState.ANSWERED if person_answer == question[
                #             call.from_user.id].answer else \
                #             questions.AnswerState.TRANSFERRED
                #         db.add(planned_question)
                #     db.commit()
