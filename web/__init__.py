from flask import Flask, redirect, render_template, request
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
