import json
import os


class Settings(dict):
    def __init__(self):
        super().__init__()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)
        return cls.instance

    def setup(self, filename, default_values: dict):
        self.file = filename

        for k, v in default_values.items():
            self.setdefault(k, v)

        if not os.path.exists(filename):
            open(filename, "w").close()

        with open(filename, "r") as file:
            try:
                self.update(json.load(file))
            except json.decoder.JSONDecodeError:
                pass

    def update_settings(self):
        with open(self.file, "w") as file:
            json.dump(self, file)
