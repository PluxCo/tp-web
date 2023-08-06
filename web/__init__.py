import datetime
import json
import os

from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO
from sqlalchemy import select, func, distinct

import schedule
import tools
from models import db_session
from models.questions import QuestionAnswer, Question, AnswerState
from models.users import Person, PersonGroup

from web.forms.users import LoginForm, UserCork, CreateGroupForm, PausePersonForm
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
    with db_session.create_session() as db:
        persons = db.scalars(select(Person)).all()
        data = []
        timeline_correct = []
        timeline_incorrect = []
        id_to_name = {}
        for person in persons:
            id_to_name[person.id] = person.full_name
            all_questions = db.scalars(select(Question).
                                       join(Question.groups).
                                       where(PersonGroup.id.in_(pg.id for pg in person.groups)).
                                       group_by(Question.id)).all()
            correct_count = 0
            answered_count = 0
            questions_count = len(all_questions)

            for current_question in all_questions:
                answers = db.scalars(select(QuestionAnswer).
                                     where(QuestionAnswer.person_id == person.id,
                                           QuestionAnswer.question_id == current_question.id,
                                           QuestionAnswer.state != AnswerState.NOT_ANSWERED).
                                     order_by(QuestionAnswer.ask_time)).all()

                if answers:
                    answered_count += 1
                    if answers[-1].question.answer == answers[-1].person_answer:
                        correct_count += 1
            data.append((person, correct_count, answered_count, questions_count))

        all_correct_answers = db.scalars(
            select(QuestionAnswer).join(Question).where(QuestionAnswer.person_answer == Question.answer)).all()
        all_incorrect_answers = db.scalars(
            select(QuestionAnswer).join(Question).where(QuestionAnswer.person_answer != Question.answer)).all()
        for answer in all_correct_answers:
            timeline_correct.append((answer.answer_time.timestamp() * 1000, answer.person_id, 5))
        for answer in all_incorrect_answers:
            timeline_incorrect.append((answer.answer_time.timestamp() * 1000, answer.person_id, 3))

        config = {"timeline_data_correct": [{"x": x, "y": y, "r": r} for x, y, r in timeline_correct],
                  "timeline_data_incorrect": [{"x": x, "y": y, "r": r} for x, y, r in timeline_incorrect],
                  "id_to_name": id_to_name}

    return render_template("index.html", data=data, config=json.dumps(config, ensure_ascii=False))


# noinspection PyTypeChecker
@app.route("/statistic/<int:person_id>", methods=["POST", "GET"])
@login_required
def statistic_page(person_id):
    with db_session.create_session() as db:
        pause_form = PausePersonForm()
        person = db.get(Person, person_id)

        person_subjects = db.scalars(select(distinct(Question.subject)).join(Question.groups).
                                     where(PersonGroup.id.in_(pg.id for pg in person.groups)))
        subject_stat = []
        bar_stat = [[], [], []]
        timeline = []

        if pause_form.pause.data and pause_form.validate():
            person.is_paused = True
            db.commit()
        if pause_form.unpause.data and pause_form.validate():
            person.is_paused = False
            db.commit()

        for name in person_subjects:
            all_questions = db.scalars(select(Question).
                                       join(Question.groups).
                                       where(Question.subject == name,
                                             PersonGroup.id.in_(pg.id for pg in person.groups)).
                                       group_by(Question.id)).all()

            correct_count = 0
            correct_count_by_level = {}
            answered_count = 0
            answered_count_by_level = {}
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

                    if answers[-1].question.level not in answered_count_by_level.keys():
                        answered_count_by_level[answers[-1].question.level] = 0
                        correct_count_by_level[answers[-1].question.level] = 0

                    answered_count_by_level[answers[-1].question.level] += 1

                    if answers[-1].state == AnswerState.TRANSFERRED:
                        answer_state = "IGNORED"
                    elif answers[-1].question.answer == answers[-1].person_answer:
                        correct_count += 1
                        correct_count_by_level[answers[-1].question.level] += 1
                        answer_state = "CORRECT"
                    else:
                        answer_state = "INCORRECT"

                person_answers.append((current_question, answer_state,
                                       question_correct_count, question_incorrect_count))

            subject_stat.append((name, correct_count, answered_count, questions_count, person_answers))
            progress_by_level = {}

            for level in answered_count_by_level:
                progress_by_level[level] = round(correct_count_by_level[level] / answered_count_by_level[level] * 100,
                                                 1)

            bar_stat[0].append(name)
            bar_stat[1].append(progress_by_level)
            if progress_by_level:
                bar_stat[2].append(max(progress_by_level, key=progress_by_level.get))
        if bar_stat[2]:
            max_level = max(bar_stat[2])
        else:
            max_level = 0
        progress_by_level = [[]]
        for i in range(1, max_level):
            progress_by_level.append([])
            for j in range(len(bar_stat[1])):
                if i in bar_stat[1][j].keys():
                    progress_by_level[i].append(bar_stat[1][j][i])
                else:
                    progress_by_level[i].append(0)

        bar_data = [bar_stat[0], progress_by_level, max_level]
        for check_time in [datetime.datetime.now() + datetime.timedelta(x / 3) for x in range(-120, 1)]:
            correct_questions_amount = db.scalar(
                select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
                                                                           QuestionAnswer.answer_time <= check_time,
                                                                           QuestionAnswer.state == AnswerState.ANSWERED,
                                                                           Question.answer == QuestionAnswer.person_answer))
            incorrect_questions_amount = db.scalar(
                select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
                                                                           QuestionAnswer.answer_time <= check_time,
                                                                           QuestionAnswer.state == AnswerState.ANSWERED,
                                                                           Question.answer != QuestionAnswer.person_answer))
            ignored_questions_amount = db.scalar(
                select(func.count(QuestionAnswer.id)).join(Question).where(QuestionAnswer.person_id == person_id,
                                                                           QuestionAnswer.ask_time <= check_time,
                                                                           QuestionAnswer.state == AnswerState.TRANSFERRED,
                                                                           QuestionAnswer.person_answer == None))

            timeline.append((check_time.timestamp() * 1000, correct_questions_amount, incorrect_questions_amount,
                             ignored_questions_amount))

        return render_template("statistic.html", person=person,
                               AnswerState=AnswerState, subjects=subject_stat,
                               timeline=timeline, bar_data=json.dumps(bar_data, ensure_ascii=False),
                               pause_form=pause_form)


@app.route("/questions", methods=["POST", "GET"])
@login_required
def questions_page():
    with db_session.create_session() as db:
        create_question_form = CreateQuestionForm()
        import_question_form = ImportQuestionForm()

        active_tab = "CREATE"

        groups = [(str(item.id), item.name) for item in db.scalars(select(PersonGroup))]
        create_question_form.groups.choices = groups
        import_question_form.groups.choices = groups

        questions_list = db.scalars(select(Question))

        if create_question_form.create.data and create_question_form.validate():
            active_tab = "CREATE"

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
            active_tab = "IMPORT"

            selected = [int(item) for item in import_question_form.groups.data]
            selected_groups = db.scalars(select(PersonGroup).where(PersonGroup.id.in_(selected))).all()

            try:
                for record in json.loads(import_question_form.import_data.data):
                    if record["answer"] not in record["options"]:
                        import_question_form.import_data.errors.append(
                            "Answer '{}' wasn't found in options".format(record["answer"]))
                        db.rollback()
                        break

                    answer = record["options"].index(record["answer"]) + 1

                    new_question = Question(text=record["question"],
                                            subject=import_question_form.subject.data,
                                            options=json.dumps(record["options"], ensure_ascii=False),
                                            answer=answer,
                                            level=record["difficulty"],
                                            article_url=import_question_form.article.data)
                    new_question.groups.extend(selected_groups)
                    db.add(new_question)
                else:
                    db.commit()

                    import_question_form = ImportQuestionForm(formdata=None,
                                                              groups=import_question_form.groups.data)
                    import_question_form.groups.choices = groups
            except (json.decoder.JSONDecodeError, KeyError) as e:
                import_question_form.import_data.errors.append(
                    "Decode error: {}".format(e))
                db.rollback()

        return render_template("question.html",
                               active_tab=active_tab,
                               questions=questions_list,
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
