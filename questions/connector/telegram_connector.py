import abc

import flask_restful

from schedule.generators import Session
from tools import Settings


class ConnectorInterface(abc.ABC):
    @abc.abstractmethod
    def transfer(self, sessions: list[Session]):
        pass


class TelegramConnector(ConnectorInterface):
    def __init__(self):
        TelegramWebhookResource.connector = self

        self.alive_sessions: list[Session] = []

    def transfer(self, sessions: list[Session]):
        print(sessions)


class TelegramWebhookResource(flask_restful.Resource):
    connector: TelegramConnector = None

    def post(self):
        pass
