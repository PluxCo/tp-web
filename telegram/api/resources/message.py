from flask_restful import Resource, reqparse
from telegram.bot.bot import send_messages


post_message_parser = reqparse.RequestParser()
post_message_parser.add_argument('messages', type=str, required=True, action='append')
post_message_parser.add_argument('webhook', type=str, required=True)


class MessageResource(Resource):
    def post(self):
        args = post_message_parser.parse_args()
        m = args.get("messages")[0].replace("'", '"')
        w = args.get("webhook")

        return {"message_ids": send_messages(m, w)}, 200
