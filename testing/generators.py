import json

import numpy as np
from faker import Faker
from sqlalchemy import select

from models.db_session import Session

from models import users, questions


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

        question.level = np.random.randint(1, 5)
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

    for group in db.scalars(select(users.PersonGroupAssociation)):
        group.target_level = np.random.randint(1, 5)
    db.commit()
