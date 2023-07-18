from web import app as web
from tools import Settings

if __name__ == '__main__':
    Settings().setup("test.json")

    Settings()["test"] = 0
    Settings().update_settings()

    # web.run()
