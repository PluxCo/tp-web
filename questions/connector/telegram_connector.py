import abc
import json

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
        request = {"webhook": "",
                   "messages": []}
        for session in sessions:
            current_question = session.next_question()
            message = {"user_id": current_question.person_id,
                       "type": "WITH_BUTTONS",
                       "data": {
                           "text": current_question.question.text,
                           "buttons": json.loads(current_question.question.options)
                       }
                       }
            request["messages"].append(message)

        print(request)


class TelegramWebhookResource(flask_restful.Resource):
    connector: TelegramConnector = None

    def post(self):
        pass
