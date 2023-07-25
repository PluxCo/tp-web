import datetime
import math
import schedule

from models import db_session
from bot import start_bot, send_question
import schedule
from models import questions,users
from sqlalchemy import select
from tools import Settings
from web import app as web

default_settings = {"tg_pin": 32266,
                    "time_period": datetime.timedelta(seconds=1),
                    "from_time": datetime.time(10),
                    "to_time": datetime.time(20),
                    "order": 1,
                    "week_days": [schedule.WeekDays.Friday],
                    "distribution_function": math.exp,
                    "repetition_amount": 6,
                    }

if __name__ == '__main__':
    Settings().setup("settings.json", default_settings)
    db_session.global_init("database.db")

    bot = start_bot()

    web.run()
