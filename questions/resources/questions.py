import json

from flask_restful import Resource, reqparse
from sqlalchemy import select, update, delete

from models import questions
from models.db_session import create_session
from resources.utils import abort_if_doesnt_exist

update_data_parser = reqparse.RequestParser()
update_data_parser.add_argument('text', type=str, required=False)
update_data_parser.add_argument('subject', type=str, required=False)
update_data_parser.add_argument('options', type=str, required=False, action='append')
update_data_parser.add_argument('answer', type=str, required=False)
update_data_parser.add_argument('groups', type=str, required=False, action='append')
update_data_parser.add_argument('level', type=int, required=False)
update_data_parser.add_argument('article_url', type=int, required=False)

create_data_parser = reqparse.RequestParser()
create_data_parser.add_argument('text', type=str, required=True)
create_data_parser.add_argument('subject', type=str, required=False)
create_data_parser.add_argument('options', type=str, required=True, action='append')
create_data_parser.add_argument('answer', type=str, required=True)
create_data_parser.add_argument('groups', type=str, required=True, action='append')
create_data_parser.add_argument('level', type=int, required=True)
create_data_parser.add_argument('article_url', type=int, required=False)


class QuestionResource(Resource):
    @abort_if_doesnt_exist("question_id", questions.Question)
    def get(self, question_id):
        with create_session() as db:
            db_question = db.get(questions.Question, question_id).to_dict(rules=("-groups.id", "-groups.question_id"))

        return db_question, 200

    @abort_if_doesnt_exist("question_id", questions.Question)
    def post(self, question_id):
        args = update_data_parser.parse_args()
        filtered_args = {k: v for k, v in args.items() if v is not None}

        if "options" in filtered_args:
            filtered_args["options"] = json.dumps(filtered_args["options"], ensure_ascii=True)

        groups = []
        if "groups" in filtered_args:
            groups = [questions.QuestionGroupAssociation(question_id=question_id, group_id=g_id)
                      for g_id in filtered_args["groups"]]
            del filtered_args["groups"]

        with create_session() as db:
            db_question = db.get(questions.Question, question_id)

            db.execute(update(questions.Question).
                       where(questions.Question.id == question_id).
                       values(filtered_args))

            if groups:
                db.execute(delete(questions.QuestionGroupAssociation).
                           where(questions.QuestionGroupAssociation.question_id == question_id))

                db_question.groups.extend(groups)

            db.commit()

        return '', 200


class AllQuestionsResource(Resource):
    def get(self):
        with create_session() as db:
            db_question = [q.to_dict(rules=("-groups.id", "-groups.question_id")) for q in
                           db.scalars(select(questions.Question))]

        return db_question, 200

    def post(self):
        with create_session() as db:
            args = create_data_parser.parse_args()
            db_question = questions.Question(text=args['text'],
                                             subject=args['subject'],
                                             options=json.dumps(args['options'], ensure_ascii=True),
                                             answer=args['answer'],
                                             level=args['level'],
                                             article_url=args['article_url'])
            db.add(db_question)
            db.commit()

            for group in args['groups']:
                db_question.groups.append(questions.QuestionGroupAssociation(question_id=db_question.id,
                                                                             group_id=group))
            db.commit()
        return '', 200
