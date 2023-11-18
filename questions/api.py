from flask import Flask
from flask_restful import Api

from models.db_session import global_init
from resources.questions import QuestionResource, AllQuestionsResource

app = Flask(__name__)
api = Api(app)


api.add_resource(QuestionResource, '/question/<int:question_id>')
api.add_resource(AllQuestionsResource, '/question/')

if __name__ == '__main__':
    global_init("data/db.db")

    app.run(debug=True, port=3000)
