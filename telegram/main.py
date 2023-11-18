from api.telegram_api import app
from telegram.bot.models import db_session

if __name__ == "__main__":
    db_session.global_init("data/database.db")

    app.run(debug=True)
