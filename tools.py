import json
import os
from typing import IO


class Settings:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)
        return cls.instance

    def setup(self, filename):
        self.file = filename
        self.data = {}

        if not os.path.exists(filename):
            open(filename, "w").close()
        else:
            with open(filename, "r") as file:
                try:
                    self.data = json.loads(file.read())
                except json.decoder.JSONDecodeError:
                    pass

    def update_settings(self):
        with open(self.file, "w") as file:
            file.write(json.dumps(self.data))

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value
        return value
