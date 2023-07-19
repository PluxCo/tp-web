import math
import random

import sqlalchemy
from faker import Faker
import json
from models.db_session import Session
from models import questions, users


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