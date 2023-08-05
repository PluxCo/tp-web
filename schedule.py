import datetime
import enum
import math
import random
import time
from abc import ABC
from collections import defaultdict
from threading import Thread
import abc

import numpy as np
from sqlalchemy import select, and_, func

from models import questions, users, db_session
from models.db_session import create_session
from models.questions import Question, QuestionAnswer, AnswerState
from models.users import Person, PersonGroup
from tools import Settings


class WeekDays(enum.Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


# def half_normal(location, standard_deviation):
#     n = np.random.normal(location, standard_deviation)
#     if n > location:
#         n2 = np.random.normal(location, standard_deviation)
#         return n2
#     return n
#
#
# def person_levels(person_id) -> dict:
#     with create_session() as db:
#         # Returns the average level of questions which were answered incorrectly
#
#         person_groups = [group.id for group in db.get(users.Person, person_id).groups]
#         group_levels = dict()
#
#         for group in person_groups:
#             correct_answers_sum = \
#                 db.query(func.sum(questions.Question.level)).join(questions.QuestionAnswer.question).filter(
#                     questions.QuestionAnswer.question.has(and_(
#                         questions.Question.answer == questions.QuestionAnswer.person_answer,
#                         questions.Question.groups.any(questions.QuestionGroupAssociation.group_id == group),
#                         questions.QuestionAnswer.person_id == person_id
#                     ))).first()[0]
#
#             correct_answers = \
#                 db.query(func.count(questions.Question.level)).join(questions.QuestionAnswer.question).filter(
#                     questions.QuestionAnswer.question.has(and_(
#                         questions.Question.answer == questions.QuestionAnswer.person_answer,
#                         questions.Question.groups.any(questions.QuestionGroupAssociation.group_id == group),
#                         questions.QuestionAnswer.person_id == person_id
#                     ))).first()[0]
#
#             group_levels[group] = round(correct_answers_sum / correct_answers if correct_answers != 0 else 1,
#                                         2)
#
#         return group_levels


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


class Schedule(Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self._callback = callback
        self._every = None
        self._order = None  # 1 if time period is calculated first and 0 in other case
        self._week_days = None
        self._distribution_function = None
        self._repetition_amount = None
        self._from_time = None
        self._to_time = None
        Settings().add_update_handler(self.from_settings)

        self.generator: GeneratorInterface = SimpleRandomGenerator()

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
            now = datetime.datetime.now()
            if self._repetition_amount is not None:
                previous_call = self._periodic_call(now, previous_call, persons)
            time.sleep(1)

    def _periodic_call(self, now, previous_call, persons):
        question_for_person = []
        if self._from_time is None or self._from_time <= now.time() <= self._to_time:
            if previous_call is None or (now >= previous_call + self._every):
                if self._order == 1:
                    previous_call = now
                if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
                    for person in persons:
                        answer = self.generator.next_question(person)
                        question_for_person.append((person, answer))

                    self._send_to_people(question_for_person)
                    previous_call = now

        return previous_call

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

# class Schedule(Thread):
#     def __init__(self, callback):
#         super().__init__(daemon=True)
#         self._callback = callback
#         self._every = None
#         self._order = None  # 1 if time period is calculated first and 0 in other case
#         self._week_days = None
#         self._distribution_function = None
#         self._repetition_amount = None
#         self._from_time = None
#         self._to_time = None
#         Settings().add_update_handler(self.from_settings)
#
#     def every(self, seconds: float = 0, minutes: float = 0, hours: float = 0,
#               days: float = 0, weeks: float = 0):
#         self._every = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
#
#         if self._order is None:
#             self._order = 1
#
#         return self
#
#     def on(self, dt: list[WeekDays] or WeekDays):
#         if type(dt) == list:
#             self._week_days = [WeekDays(x) for x in dt]
#         else:
#             self._week_days = [WeekDays(dt)]
#         if self._order is None:
#             self._order = 0
#
#         return self
#
#     def using_repetition_function(self, distribution_function=math.exp, repetition_amount=6):
#         self._distribution_function = distribution_function
#         self._repetition_amount = repetition_amount
#
#         return self
#
#     def from_settings(self):
#         self._every = Settings()['time_period']
#         self._order = Settings()['order']
#         self._week_days = Settings()['week_days']
#         self._distribution_function = Settings()['distribution_function']
#         self._repetition_amount = Settings()['repetition_amount']
#         self._from_time = Settings()['from_time']
#         self._to_time = Settings()['to_time']
#
#         return self
#
#     def run(self) -> None:
#         """The run function of a schedule thread. Note that the order in which you call methods matters.
#          on().every() and every().on() play different roles. They in somewhat way mask each-other."""
#         db = create_session()
#         previous_call = None
#         while True:
#             persons = db.scalars(select(users.Person)).all()
#             now = datetime.datetime.now()
#             if self._repetition_amount is not None:
#                 previous_call = self._periodic_call(now, previous_call, persons)
#             time.sleep(1)
#
#     def _random_question(self, person_id: int) -> int:
#
#         with create_session() as db:
#             groups = db.scalars(
#                 select(users.PersonGroupAssociation).where(users.PersonGroupAssociation.person_id == person_id)).all()
#             search_window = datetime.timedelta(self._distribution_function(self._repetition_amount))
#
#             all_planned_question_ids = [(answer.question_id, answer.question.level) for answer in db.scalars(
#                 select(questions.QuestionAnswer).
#                 where(questions.QuestionAnswer.state == questions.AnswerState.NOT_ANSWERED))]
#
#             answered_question_ids = [(answer.question_id, answer.question.level) for answer in db.scalars(
#                 select(questions.QuestionAnswer).where(questions.QuestionAnswer.person_id == person_id).where(
#                     questions.QuestionAnswer.ask_time > datetime.datetime.now() - search_window,
#                     questions.QuestionAnswer.state == questions.AnswerState.ANSWERED))]
#
#             group_level_differences = dict()
#             current_levels = person_levels(person_id)
#             question_ids = []
#
#             for group in groups:
#                 group_level_differences[group.group_id] = group.target_level - current_levels[group.group_id]
#
#             for worst_group_id in sorted(group_level_differences, key=group_level_differences.get, reverse=True):
#                 question_ids = [(question.id, question.level) for question in db.scalars(
#                     select(questions.Question).join(questions.Question.groups).where(
#                         users.PersonGroup.id == worst_group_id))]
#
#                 #  Find intersection of questions to ask and questions which were asked earlier or planned
#                 #
#                 result_list = list(
#                     set(question_ids).difference(answered_question_ids).difference(all_planned_question_ids))
#                 if not result_list:
#                     continue  # continue the loop if the result list is already empty
#
#                 for _ in range(10):  # Trying to generate appropriate question (Completely dumb idea, but eh)
#                     question_level = round(
#                         half_normal(current_levels[worst_group_id], 1))  # Generating appropriate question level
#                     if question_level <= 0:
#                         question_level = 1  # Check if the question level is positive otherwise chose the lowest
#                     result_list = list(filter(lambda x: x[1] == question_level, result_list))
#                     # print(result_list)
#                     if result_list:
#                         break  # If the generating was successful
#
#                 if len(result_list) != 0:
#                     break  # If a group with questions to ask was found
#
#             if len(question_ids) == 0:
#                 # If we didn't find correct questions to ask then
#                 # select all the questions from these groups
#                 groups_n = [group.group_id for group in groups]
#                 question_ids = [question.id for question in db.scalars(
#                     select(questions.Question).join(questions.Question.groups).where(
#                         users.PersonGroup.id.in_(groups_n)))]
#
#             if not question_ids:
#                 return 0
#
#             if len(result_list) > 0:
#                 question = random.choice(result_list)[0]
#             else:
#                 question = random.choice(question_ids)[0]
#
#             # Add questions to the database as planned
#             #
#             planned_question = questions.QuestionAnswer()
#             planned_question.ask_time = datetime.datetime.now()
#             planned_question.question_id = question
#             planned_question.person_id = person_id
#             planned_question.state = questions.AnswerState.NOT_ANSWERED
#             db.add(planned_question)
#             db.commit()
#
#             return question
#
#     def _plan_questions(self, person_id: int):
#         with create_session() as db:
#             answers_map = defaultdict(list)
#             questions_to_ask = []
#             questions_to_ask_now = []
#
#             if db.get(users.Person, person_id).is_paused:
#                 return questions_to_ask_now
#
#             answered_questions = db.scalars(
#                 select(questions.QuestionAnswer).join(questions.QuestionAnswer.question).where(and_(
#                     questions.QuestionAnswer.person_id == person_id,
#                     questions.QuestionAnswer.state == questions.AnswerState.ANSWERED,
#                     questions.Question.answer == questions.QuestionAnswer.person_answer)).order_by(
#                     questions.QuestionAnswer.ask_time.desc())).all()
#
#             planned_questions = db.scalars(
#                 select(questions.QuestionAnswer).where(questions.QuestionAnswer.person_id == person_id).where(
#                     questions.QuestionAnswer.state == questions.AnswerState.NOT_ANSWERED).order_by(
#                     questions.QuestionAnswer.ask_time.desc())).all()
#
#             for answer in planned_questions:  # Add questions which were planned to ask before to the list
#                 questions_to_ask.append(answer.question_id)
#                 if answer.ask_time <= datetime.datetime.now():
#                     questions_to_ask_now.append(answer.question_id)
#
#             for answer in answered_questions:  # Add questions which were not planned yet to the map of questions for repeat
#                 if answer.question_id not in questions_to_ask:
#                     answers_map[answer.question_id].append(answer)
#
#             for key in answers_map:  # Add questions which require repetition to the database as planed
#                 length = len(answers_map[key])
#                 if length < self._repetition_amount:
#                     delta = datetime.timedelta(self._distribution_function(length))
#                     planned_answer = questions.QuestionAnswer()
#                     planned_answer.ask_time = delta + answers_map[key][0].ask_time
#                     planned_answer.state = questions.AnswerState.NOT_ANSWERED
#                     planned_answer.question_id = key
#                     planned_answer.person_id = person_id
#                     db.add(planned_answer)
#
#             db.commit()
#             return questions_to_ask_now
#
#     def _periodic_call(self, now, previous_call, persons):
#         question_for_person = {}
#
#         if self._from_time is None or self._from_time <= now.time() <= self._to_time:
#             if previous_call is None or (now >= previous_call + self._every):
#                 if self._order == 1:
#                     previous_call = now
#                 if self._week_days is None or (WeekDays(now.weekday()) in self._week_days):
#                     for person in persons:
#                         questions_to_ask_now = self._plan_questions(person.id)
#                         if len(questions_to_ask_now) != 0:
#                             question_for_person[person.id] = np.random.choice(questions_to_ask_now)
#                         else:
#                             question_for_person[person.id] = self._random_question(person.id)
#                     self._send_to_people(question_for_person)
#                     previous_call = now
#
#         return previous_call
#
#     def _send_to_people(self, question_to_person):
#         with create_session() as db:
#             for person_id in question_to_person:
#                 question_id = int(question_to_person[person_id])
#                 if not question_id:
#                     return
#
#                 person_id: int
#
#                 question = db.get(questions.Question, int(question_id))
#                 person = db.get(users.Person, person_id)
#
#                 if person.is_paused:
#                     return
#
#                 answer = db.scalars(select(questions.QuestionAnswer).where(
#                     questions.QuestionAnswer.question_id == question.id).where(
#                     questions.QuestionAnswer.person_id == person_id).where(
#                     questions.QuestionAnswer.state == questions.AnswerState.NOT_ANSWERED).order_by(
#                     questions.QuestionAnswer.ask_time)).first()
#                 answer.state = questions.AnswerState.TRANSFERRED  # Mark an answer as transferred (sent)
#                 db.commit()
#
#                 self._callback(person, answer)  # Send a question to a person
