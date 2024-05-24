import datetime
import logging
import os

import requests

logger = logging.getLogger(__name__)


class Settings:
    def __init__(self, pin: str, session_duration: datetime.timedelta, max_interactions: int):
        self.max_interactions = max_interactions
        self.session_duration = session_duration
        self.pin = pin


class SettingsDAO:
    __resource = '{}/settings/'
    __host = os.getenv("TELEGRAM_URL", "http://localhost:3001")

    @staticmethod
    def set_host(resource: str):
        SettingsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Settings(resp['password'],
                     datetime.timedelta(seconds=resp['session_duration']),
                     resp['amount_of_questions'])
        return q

    @staticmethod
    def get_settings() -> Settings:
        resp = requests.get(SettingsDAO.__resource.format(SettingsDAO.__host)).json()
        return SettingsDAO._construct(resp)

    @staticmethod
    def update_settings(settings: Settings):
        req = {
            "password": settings.pin,
            "session_duration": settings.session_duration.total_seconds(),
            "amount_of_questions": settings.max_interactions
        }

        resp = requests.patch(SettingsDAO.__resource.format(SettingsDAO.__host), json=req)

        if resp.status_code != 200:
            logger.error("Failed to update settings: %s with request %s", resp.text, req)
