import datetime
import logging
import os

import requests

logger = logging.getLogger(__name__)


class Settings:
    def __init__(self, pin: str, session_duration: datetime.timedelta, max_interactions: int,
                 period: datetime.timedelta, start_time: datetime.time, end_time: datetime.time):
        self.max_interactions = max_interactions
        self.session_duration = session_duration
        self.pin = pin

        self.period = period
        self.start_time = start_time
        self.end_time = end_time


class SettingsDAO:
    __resource = '{}/settings/'
    __host = os.getenv("TELEGRAM_URL", "http://localhost:3001")

    @staticmethod
    def set_host(resource: str):
        SettingsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Settings(resp['password'],
                     datetime.timedelta(seconds=float(resp['session_duration'])),
                     resp['amount_of_questions'],
                     datetime.timedelta(seconds=resp['period']),
                     datetime.time.fromisoformat(resp["start_time"]),
                     datetime.time.fromisoformat(resp["end_time"]))
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
            "amount_of_questions": settings.max_interactions,
            "period": settings.period.total_seconds(),
            "start_time": settings.start_time.isoformat(),
            "end_time": settings.end_time.isoformat()
        }

        resp = requests.patch(SettingsDAO.__resource.format(SettingsDAO.__host), json=req)

        if resp.status_code != 200:
            logger.error("Failed to update settings: %s with request %s", resp.text, req)
