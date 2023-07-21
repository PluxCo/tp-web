import datetime, enum, math, time, json
import numpy as np
from collections import defaultdict

from sqlalchemy import select, and_, or_
from faker import Faker
from models.db_session import Session, create_session
from models import questions, users
from tools import Settings
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


def random_question(person_id: int, group_id: list or int = None) -> int:
    """Gives random question id within the same group, which hasn't been asked yet otherwise returns -1"""

    with create_session() as db:
        person = db.scalar(select(users.Person).where(users.Person.id == person_id))
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
            select(questions.QuestionAnswer).where(questions.QuestionAnswer.person_id == person_id))]

        result_list = list(set(question_ids).difference(answered_question_ids))
        if len(result_list) > 0:
            return np.random.choice(result_list)
        else:
            return -1


def repetition_function(person_id: int, now=datetime.datetime.now(), period_function=math.exp):
    repetition_amount = 6

    db = create_session()
    answers_map = defaultdict(list)
    questions_to_ask = []
    questions_to_ask_now = []

    answers_timeline = db.scalars(
        select(questions.QuestionAnswer).where(and_(questions.QuestionAnswer.person_id == person_id,
                                                    questions.QuestionAnswer.state == questions.AnswerState.ANSWERED)).order_by(
            questions.QuestionAnswer.ask_time.desc())).all()

    for answer in answers_timeline:
        answers_map[answer.question_id].append(answer)

    for key in answers_map:
        length = len(answers_map[key])
        if length < repetition_amount:
            delta = datetime.timedelta(period_function(length))
            questions_to_ask.append((key, delta))
            if delta + answers_map[key][0].ask_time - datetime.timedelta(seconds=1) <= now <= delta + answers_map[key][
                0].ask_time + datetime.timedelta(seconds=1):
                questions_to_ask_now.append(key)

    return questions_to_ask_now, questions_to_ask


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
        self._distribution_function = None
        self._repetition_amount = None

    def every(self, seconds: float = 0, minutes: float = 0, hours: float = 0,
              days: float = 0, weeks: float = 0, months: float = 0):
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

    def using_repetition_function(self, distribution_function=math.exp, repetition_amount=6):
        self._distribution_function = distribution_function
        self._repetition_amount = repetition_amount

        return self

    def from_settings(self):
        self._every = {'delta': Settings()['time_period']}
        self._order = Settings()['order']
        self._week_days = Settings()['week_days']
        self._distribution_function = Settings()['distribution_function']
        self._repetition_amount = Settings()['repetition_amount']

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
                    questions_to_ask_now = repetition_function(person.id, now, self._distribution_function)[0]
                    if len(questions_to_ask_now) != 0:
                        question_for_person[person.id] = np.random.choice(questions_to_ask_now)
                    else:
                        question_for_person[person.id] = random_question(person.id)
                previous_call = self._periodic_call(now, previous_call, question_for_person)
            else:
                for person in persons:
                    question_for_person[person.id] = random_question(person.id)
                previous_call = self._periodic_call(now, previous_call, question_for_person)
            time.sleep(1)

    def _periodic_call(self, now, previous_call, args):
        if self._order == 1:
            if previous_call is None or ('month' in self._every.keys() and (
                    (previous_call.month + self._every['month']) % 12 + 1) >= now.month):
                if previous_call is None or (now >= previous_call + self._every['delta']):
                    previous_call = now
                    if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                        self._send_to_people(args)
                        previous_call = now
            elif 'month' not in self._every.keys():
                if previous_call is None or (now >= previous_call + self._every['delta']):
                    previous_call = now
                    if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                        self._send_to_people(args)
                        previous_call = now
        if self._order == 0:
            if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                if previous_call is None or (now >= previous_call + self._every['delta']):
                    self._send_to_people(args)
                    previous_call = now
        return previous_call

    def _send_to_people(self, question_to_person):
        with create_session() as db:
            for person_id in question_to_person:
                question_id = question_to_person[person_id]
                question = db.get(questions.Question, int(question_id))
                person = db.get(users.Person, person_id)
                self._callback(person, question)
