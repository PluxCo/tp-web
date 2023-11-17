class Person:
    def __init__(self, user_id: str, groups: list[tuple[str, int]]):
        self.id = user_id
        self.groups = groups

    def __repr__(self):
        return f"Person(id={self.id}, groups={self.groups})"
