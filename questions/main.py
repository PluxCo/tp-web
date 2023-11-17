import datetime

import requests

import schedule
from generators import Session
from models import db_session
from models.users import Person
from tools import Settings


def get_all_people():
    resp = requests.get("http://localhost:9011/api/user/search?queryString=*",
                        headers={"Authorization": "CUt_rIp3_acxcGYZ8rBHE7ZOZCOTMAmRb2J5Fwf_EToAMWQBRNRlTvpx"}).json()

    res = []

    for person in resp["users"]:
        person_id = person["id"]
        all_groups = [m["groupId"] for m in person["memberships"]]

        if "groupLevels" in person["data"]:
            person_groups = [(item["groupId"], item["level"]) for item in person["data"]["groupLevels"]
                             if item["groupId"] in all_groups]

            yield Person(person_id, person_groups)
        else:
            yield Person(person_id, [])


sessions = {}


def create_session():
    for person in get_all_people():
        session = Session(person, Settings()["max_time"], Settings()["max_questions"])
        session.generate_questions()
        print(session.next_question())


default_settings = {"tg_pin": "32266",
                    "time_period": datetime.timedelta(seconds=30),
                    "from_time": datetime.time(0),
                    "to_time": datetime.time(23, 59),
                    "order": 1,
                    "week_days": [d for d in range(7)],
                    "max_time": datetime.timedelta(minutes=1),
                    "max_questions": 1,
                    }

if __name__ == '__main__':
    Settings().setup("data/settings.stg", default_settings)
    db_session.global_init("data/database.db")

    schedule.Schedule(create_session).from_settings().start()

    while True:
        pass
