import requests
import os


class Person:
    def __init__(self, user_id: str, groups: list[tuple[str, int]]):
        self.id = user_id
        self.groups = groups

    @staticmethod
    def get_all_people():
        resp = requests.get(f"{os.getenv('FUSIONAUTH_DOMAIN')}/api/user/search?queryString=*",
                            headers={"Authorization": os.getenv("FUSIONAUTH_TOKEN")})

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        resp = resp.json()

        for person in resp["users"]:
            person_id = person["id"]
            all_groups = [m["groupId"] for m in person["memberships"]]

            if "groupLevels" in person["data"]:
                person_groups = [(item["groupId"], item["level"]) for item in person["data"]["groupLevels"]
                                 if item["groupId"] in all_groups]

                yield Person(person_id, person_groups)
            else:
                yield Person(person_id, [])

    def __repr__(self):
        return f"Person(id={self.id}, groups={self.groups})"
