import os

from flask import Flask, redirect, render_template, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from models.users_forms import LoginForm, UserCork

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return UserCork()


@app.route("/login", methods=["POST", "GET"])
def login_page():
    login_form = LoginForm()
    error = None

    if login_form.validate_on_submit():
        if login_form.passwd.data == os.environ.get("ADMIN_PASSWD"):
            login_user(UserCork())
            return redirect("/")
        else:
            error = "Incorrect password"

    return render_template("login.html", form=login_form, error_msg=error)


@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout_page():
    logout_user()
    return redirect('/login')


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html")


@app.route("/")
def main_page():
    if not current_user.is_authenticated:
        return redirect("/login")

    return render_template("index.html")
