import datetime
import math
import schedule

from models import db_session
from bot import start_bot, send_question
import schedule
from tools import Settings
from web import app as web
from web import socketio

# Environment variables
# ADMIN_PASSWD: password for web panel
# TGTOKEN: token for telegram bot


default_settings = {"tg_pin": "32266",
                    "time_period": datetime.timedelta(days=1),
                    "from_time": datetime.time(7),
                    "to_time": datetime.time(20),
                    "order": 1,
                    "week_days": [schedule.WeekDays(d) for d in range(7)],
                    "distribution_function": math.exp,
                    "repetition_amount": 6,
                    }

if __name__ == '__main__':
    Settings().setup("data/settings.stg", default_settings)
    db_session.global_init("data/database.db")

    schedule.Schedule(send_question).from_settings().start()

    bot = start_bot()

    socketio.run(web, host="0.0.0.0", debug=True, use_reloader=False)
