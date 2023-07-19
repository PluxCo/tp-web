from web import app as web
from tools import Settings
from models import db_session

if __name__ == '__main__':
    Settings().setup("settings.json")
    db_session.global_init("database.db")

    web.run()
