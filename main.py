from web import app as web
from tools import Settings
from models import db_session
from bot import start_bot, send_question
import schedule
from models import questions,users

default_settings = {"tg_pin": 32266}

if __name__ == '__main__':
    Settings().setup("settings.json", default_settings)
    db_session.global_init("database.db")

    bot = start_bot()
    # schedule.fake_db(db_session.create_session())


    web.run()



