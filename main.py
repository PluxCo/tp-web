from web import app as web
from tools import Settings
from models import db_session

default_settings = {"tg_key": 32266}

if __name__ == '__main__':
    Settings().setup("settings.json", default_settings)
    db_session.global_init("database.db")

    web.run()
