from flask_restful import Resource, reqparse
from sqlalchemy import select

from models.questions import QuestionAnswer
from models.db_session import create_session
from api.utils import abort_if_doesnt_exist

fields_parser = reqparse.RequestParser()
fields_parser.add_argument('person_id', type=str, required=False)
fields_parser.add_argument('question_id', type=int, required=False)


class AnswerResource(Resource):
    @abort_if_doesnt_exist("answer_id", QuestionAnswer)
    def get(self, answer_id):
        with create_session() as db:
            db_answer = db.get(QuestionAnswer, answer_id).to_dict(rules=("-question",))
        return db_answer, 200


class AnswerListResource(Resource):
    def get(self):
        args = {k: v for k, v in fields_parser.parse_args().items() if v is not None}
        with create_session() as db:
            answers = [a.to_dict(rules=("-question", )) for a in db.scalars(select(QuestionAnswer).filter_by(**args))]

        return answers, 200
