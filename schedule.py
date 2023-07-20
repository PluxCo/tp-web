import datetime
import enum
import math, time

import sqlalchemy
from faker import Faker
import json
from models.db_session import Session
from models import questions, users
from threading import Thread


def fake_db(session: Session, scale=100):
    fake = Faker('ru_RU')
    db = session
    group_list = []
    question_list = []
    person_list = []

    for i in range(0, int(math.log(scale) + 1)):
        group = users.PersonGroup()
        group.name = fake.word()
        group_list.append(group)
        db.add(group)
    db.commit()

    for i in range(0, scale):
        person = users.Person()
        person.full_name = fake.name()
        person.tg_id = fake.random_int(min=1_000_000, max=1_000_000_000)
        person.level = fake.random_int(min=1, max=5)
        person.groups.append(fake.random_element(elements=group_list))
        person_list.append(person)
        db.add(person)
    db.commit()

    for i in range(0, scale * 10):
        question = questions.Question()
        question.text = fake.sentence()

        options = [fake.sentence(), fake.sentence(), fake.sentence(), fake.sentence()]
        question.options = json.dumps(options, ensure_ascii=False)
        question.answer = fake.random_element(elements=options)

        question.level = fake.random_int(min=1, max=5)
        question.article_url = fake.url()
        question.groups.append(fake.random_element(elements=group_list))
        question_list.append(question)
        db.add(question)
    db.commit()

    for i in range(0, scale * 10):
        answer = questions.QuestionAnswer()
        answer.question = fake.random_element(elements=question_list)
        answer.question_id = answer.question.id
        answer.person = fake.random_element(elements=person_list)
        answer.answered_time = fake.date_time_this_year()
        answer.ask_time = answer.answered_time
        answer.person_id = answer.person.id
        answer.state = questions.AnswerState(fake.random_int(min=0, max=2))
        db.add(answer)
    db.commit()


class WeekDays(enum.Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Sunday = 5
    Saturday = 6


class Schedule(Thread):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._every = {}
        self._order = None  # 1 if time period is calculated first and 0 in other case
        self._week_days = None

    def every(self, seconds: float = 0,
              minutes: float = 0,
              hours: float = 0,
              days: float = 0,
              weeks: float = 0,
              months: float = 0):
        if months != 0:
            self._every['months'] = months
        self._every['delta'] = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)

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

    def run(self) -> None:
        previous_call = None
        while True:
            now = datetime.datetime.now()
            if self._order == 1:
                if previous_call is None or ('month' in self._every.keys() and (
                        (previous_call.month + self._every['month']) % 12 + 1) >= now.month):
                    if previous_call is None or (now >= previous_call + self._every['delta']):
                        if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                            self._callback()
                            previous_call = now
                elif 'month' not in self._every.keys():
                    if previous_call is None or (now >= previous_call + self._every['delta']):
                        if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                            self._callback()
                            previous_call = now
            if self._order == 0:
                if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                    if previous_call is None or (now >= previous_call + self._every['delta']):
                        self._callback()
                        previous_call = now
            time.sleep(1)
