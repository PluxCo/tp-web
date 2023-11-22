import enum
import json
import os

from flask_restful import Resource, reqparse
import requests

from connector.base_connector import ConnectorInterface
from models.questions import QuestionAnswer
from schedule.generators import Session


class AnswerType(enum.Enum):
    BUTTON = 0
    MESSAGE = 1
    REPLY = 2


class TelegramConnector(ConnectorInterface):
    TG_API = os.getenv("TELEGRAM_API")

    def __init__(self, webhook: str):
        TelegramWebhookResource.connector = self
        self.webhook = webhook

        self.alive_sessions: dict[int, tuple[Session, QuestionAnswer]] = {}

    def transfer(self, sessions: list[Session]):
        request = {"webhook": self.webhook,
                   "messages": []}

        message_relation = []

        for session in sessions:
            current_question = session.next_question()
            if current_question is not None:
                message = {
                    "user_id": current_question.person_id,
                    "type": "WITH_BUTTONS",
                    "data": {
                        "text": current_question.question.text,
                        "buttons": json.loads(current_question.question.options)
                    }
                }
                request["messages"].append(message)
                message_relation.append((session, current_question))

        resp = requests.post(f"{self.TG_API}/message", json=request)

        for i, message_id in enumerate(resp.json()["message_ids"]):
            if message_id is not None:
                self.alive_sessions[message_id] = message_relation[i]
                # FIXME: status doesnt change
                message_relation[i][0].mark_question_as_transferred(message_relation[i][1])

    def register_answer(self, user_id: str, data_type: AnswerType, data: dict):
        match data_type:
            case AnswerType.BUTTON:
                session = self.alive_sessions.pop(data["message_id"])
            case AnswerType.REPLY:
                pass
            case AnswerType.MESSAGE:
                pass


class TelegramWebhookResource(Resource):
    connector: TelegramConnector = None

    answer_parser = reqparse.RequestParser()
    answer_parser.add_argument("user_id", type=str, required=True)
    answer_parser.add_argument("type", type=AnswerType, required=True)
    answer_parser.add_argument("data", type=dict, required=True)

    def post(self):
        args = self.answer_parser.parse_args()
        self.connector.register_answer(args["user_id"], args["type"], args["data"])
        return '', 200
