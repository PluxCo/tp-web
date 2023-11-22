from api.telegram_api import app
from models import db_session
import bot


if __name__ == "__main__":
    db_session.global_init("data/database.db")



    bot = bot.start_bot()
    app.run(debug=False, port=3000)
