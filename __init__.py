import json
import os

from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from wtforms.validators import ValidationError
from sqlalchemy import select, exists

from models import db_session
from models import users, questions
from web.forms.users import LoginForm, UserCork, CreateGroupForm
from web.forms.questions import CreateQuestionForm

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


@app.route("/")
def main_page():
    if not current_user.is_authenticated:
        return redirect("/login")

    return render_template("index.html")


@app.route("/add_question", methods=["POST", "GET"])
def add_question_page():
    db = db_session.create_session()
    create_question_form = CreateQuestionForm()

    groups = [(str(item.id), item.name) for item in db.scalars(select(users.PersonGroup))]
    create_question_form.groups.choices = groups

    if create_question_form.validate_on_submit():
        selected = [int(item) for item in create_question_form.groups.data]
        selected_groups = db.scalars(select(users.PersonGroup).where(users.PersonGroup.id.in_(selected)))
        options = json.dumps(create_question_form.options.data.splitlines(), ensure_ascii=False)
        new_question = questions.Question(text=create_question_form.text.data,
                                          subject=create_question_form.subject.data,
                                          options=options,
                                          answer=create_question_form.answer.data - 1,
                                          level=create_question_form.level.data,
                                          article_url=create_question_form.article.data)

        new_question.groups.extend(selected_groups)
        db.add(new_question)
        db.commit()

        create_question_form = CreateQuestionForm(formdata=None,
                                                  subject=create_question_form.subject.data,
                                                  article=create_question_form.article.data)
        create_question_form.groups.choices = groups

    questions_list = db.scalars(select(questions.Question))

    return render_template("add_question.html", questions=questions_list, create_question_form=create_question_form)


@app.route("/settings", methods=["POST", "GET"])
def settings_page():
    db = db_session.create_session()
    create_group_form = CreateGroupForm()

    if create_group_form.validate_on_submit():
        new_user = users.PersonGroup()
        new_user.name = create_group_form.name.data
        db.add(new_user)
        db.commit()

        create_group_form = CreateGroupForm(formdata=None)

    groups = db.scalars(select(users.PersonGroup))
    return render_template("settings.html", create_group_form=create_group_form, groups=groups)
