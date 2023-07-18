from web import app as web
from tools import Settings

if __name__ == '__main__':
    Settings().setup("settings.json")

    web.run()
