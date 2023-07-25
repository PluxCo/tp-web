from web import app as web
from tools import Settings
from models import db_session
from bot import start_bot, send_question
import schedule
from models import questions,users
from sqlalchemy import select

default_settings = {"tg_pin": 32266}

if __name__ == '__main__':
    Settings().setup("settings.json", default_settings)
    db_session.global_init("database.db")

    bot = start_bot()
    with db_session.create_session() as db:
        person = db.scalar(select(users.Person).where(users.Person.id == 104))
        question = db.scalar(select(questions.Question).where(questions.Question.id == 1))
    send_question(person, question)



    web.run()



