import json
import os
import itertools

from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import aliased

import schedule
import tools
from models import db_session

from models.questions import QuestionAnswer, Question, QuestionGroupAssociation, AnswerState
from models.users import Person, PersonGroup

from web.forms.users import LoginForm, UserCork, CreateGroupForm
from web.forms.questions import CreateQuestionForm, ImportQuestionForm
from web.forms.settings import TelegramSettingsForm, ScheduleSettingsForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

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


# noinspection PyTypeChecker
@app.route("/statistic/<int:person_id>")
def statistic_page(person_id):
    with db_session.create_session() as db:
        person = db.scalars(select(Person).where(Person.id == person_id)).first()

        person_subjects = db.scalars(select(distinct(Question.subject)).join(Question.groups).
                                     where(PersonGroup.id.in_(pg.id for pg in person.groups)))

        subject_stat = []

        for name in person_subjects:
            all_questions = db.scalars(select(Question).
                                       join(Question.groups).
                                       where(Question.subject == name,
                                             PersonGroup.id.in_(pg.id for pg in person.groups)).
                                       group_by(Question.id)).all()

            correct_count = 0
            answered_count = 0
            questions_count = len(all_questions)
            person_answers = []

            for current_question in all_questions:
                answers = db.scalars(select(QuestionAnswer).
                                     where(QuestionAnswer.person_id == person.id,
                                           QuestionAnswer.question_id == current_question.id,
                                           QuestionAnswer.state != AnswerState.NOT_ANSWERED).
                                     order_by(QuestionAnswer.ask_time)).all()

                question_correct_count = len([1 for a in answers if a.person_answer == current_question.answer])
                question_incorrect_count = len(answers) - question_correct_count

                answer_state = "NOT_ANSWERED"
                if answers:
                    answered_count += 1
                    if answers[-1].state == AnswerState.TRANSFERRED:
                        answer_state = "IGNORED"
                    elif answers[-1].question.answer == answers[-1].person_answer:
                        correct_count += 1
                        answer_state = "CORRECT"
                    else:
                        answer_state = "INCORRECT"

                person_answers.append((current_question, answer_state,
                                       question_correct_count, question_incorrect_count))

            subject_stat.append((name, correct_count, answered_count, questions_count, person_answers))

        return render_template("statistic.html", person=person,
                               AnswerState=AnswerState, subjects=subject_stat)


@app.route("/questions", methods=["POST", "GET"])
@login_required
def questions_page():
    db = db_session.create_session()
    create_question_form = CreateQuestionForm()
    import_question_form = ImportQuestionForm()

    groups = [(str(item.id), item.name) for item in db.scalars(select(PersonGroup))]
    create_question_form.groups.choices = groups
    import_question_form.groups.choices = groups

    if create_question_form.create.data and create_question_form.validate():
        selected = [int(item) for item in create_question_form.groups.data]
        selected_groups = db.scalars(select(PersonGroup).where(PersonGroup.id.in_(selected)))
        options = json.dumps(create_question_form.options.data.splitlines(), ensure_ascii=False)
        new_question = Question(text=create_question_form.text.data,
                                subject=create_question_form.subject.data,
                                options=options,
                                answer=create_question_form.answer.data,
                                level=create_question_form.level.data,
                                article_url=create_question_form.article.data)

        new_question.groups.extend(selected_groups)
        db.add(new_question)
        db.commit()

        create_question_form = CreateQuestionForm(formdata=None,
                                                  subject=create_question_form.subject.data,
                                                  article=create_question_form.article.data)
        create_question_form.groups.choices = groups

    if import_question_form.import_btn.data and import_question_form.validate():
        pass

    questions_list = db.scalars(select(Question))

    return render_template("question.html", questions=questions_list,
                           create_question_form=create_question_form,
                           import_question_form=import_question_form)


@app.route("/settings", methods=["POST", "GET"])
@login_required
def settings_page():
    db = db_session.create_session()
    create_group_form = CreateGroupForm()
    tg_settings_form = TelegramSettingsForm(data=tools.Settings())
    schedule_settings_form = ScheduleSettingsForm(data=tools.Settings(),
                                                  week_days=[d.value for d in tools.Settings()["week_days"]])

    if create_group_form.create_group.data and create_group_form.validate():
        new_group = PersonGroup()
        new_group.name = create_group_form.name.data
        db.add(new_group)
        db.commit()

        return redirect("/settings")

    if tg_settings_form.save_tg.data and tg_settings_form.validate():
        settings = tools.Settings()
        settings["tg_pin"] = tg_settings_form.tg_pin.data

        settings.update_settings()
        return redirect("/settings")

    if schedule_settings_form.save_schedule.data and schedule_settings_form.validate():
        settings = tools.Settings()
        settings["time_period"] = schedule_settings_form.time_period.data
        settings["week_days"] = [schedule.WeekDays(d) for d in schedule_settings_form.week_days.data]
        settings["from_time"] = schedule_settings_form.from_time.data
        settings["to_time"] = schedule_settings_form.to_time.data

        settings.update_settings()
        return redirect("/settings")

    groups = db.scalars(select(PersonGroup))
    return render_template("settings.html", create_group_form=create_group_form, groups=groups,
                           schedule_settings_form=schedule_settings_form,
                           tg_settings_form=tg_settings_form)
