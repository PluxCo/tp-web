from flask import Flask
from flask_restful import Api
from .resources.message import MessageResource


app = Flask(__name__)
api = Api(app)


api.add_resource(MessageResource, "/message/")


