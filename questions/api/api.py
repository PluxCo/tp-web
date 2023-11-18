from datetime import datetime

from flask import Flask
from flask_restful import Api

from models.db_session import global_init, create_session
from models.questions import QuestionAnswer, AnswerState
from resources.questions import QuestionResource, QuestionsListResource
from resources.answer import AnswerResource, AnswerListResource

app = Flask(__name__)
api = Api(app)


api.add_resource(QuestionResource, '/question/<int:question_id>')
api.add_resource(QuestionsListResource, '/question/')
api.add_resource(AnswerResource, "/answer/<int:answer_id>")
api.add_resource(AnswerListResource, "/answer/")

if __name__ == '__main__':
    global_init("../data/db.db")

    # with create_session() as db:
    #     a = QuestionAnswer(question_id=1, person_id="hgjhg", person_answer=1, ask_time=datetime.now(), state=AnswerState.NOT_ANSWERED)
    #     db.add(a)
    #     db.commit()

    app.run(debug=True, port=3000)
