import datetime
import json
import os
from threading import Thread

from sqlalchemy import select

from models import db_session
from models import users, questions
from models.users import Person
from tools import Settings
from web.forms.users import LoginForm, UserCork, CreateGroupForm
from models.questions import Question, QuestionAnswer
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, ReplyKeyboardMarkup, \
    KeyboardButton
import time

bot = telebot.TeleBot(os.environ['TGTOKEN'])
people = dict()
question = dict()


@bot.message_handler(commands=["start"])
def start_handler(message):
    start_markup = InlineKeyboardMarkup()
    start_markup.add(InlineKeyboardButton(text='Начать', callback_data='start'))
    bot.send_message(message.from_user.id,
                     'Привет, я бот для тестирования сотрудников 3divi. Перед началом тебе нужно ответить на пару '
                     'вопросов.', reply_markup=start_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('start') or call.data.startswith('end'))
def submit_buttons(call: CallbackQuery):
    if call.data == "start":
        # bot.send_sticker(call.message.chat.id,
        #                  'CAACAgIAAxkBAAKNcWS5VJzS8g3EFokDZRtF_6HdZeCWAALDEQACBAfQSWPVxMPrmkD0LwQ')
        message = bot.send_message(call.message.chat.id, 'Введите код доступа')
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        bot.register_next_step_handler(message, password_check)

    elif call.data == 'end_of_register':
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        add_new_person(call)


def password_check(message: Message):
    if message.text == Settings()["tg_pin"]:
        person_in_db = False
        with db_session.create_session() as db:
            if db.scalar(select(users.Person).where(users.Person.tg_id == message.chat.id)):
                person_in_db = True
        if not person_in_db:
            msg = bot.send_message(message.chat.id, 'Как тебя зовут(ФИО)?')
            # bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAKNdWS5VU9aptwvRzgZnng9_waAUpSWAAL1FAAC8Dr5SCliLP4jSEFJLwQ')
            bot.register_next_step_handler(msg, get_information_about_person)
        else:
            bot.send_message(message.chat.id, 'Вы уже зарегестрированы.')
    else:
        # bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAKNc2S5VOMaQNdzv8bNlXYOuk7r-TSvAALfLAACtZXJS9iN5C8p9Y2cLwQ')
        msg = bot.send_message(message.chat.id, 'Неверный код доступа. Попробуйте ещё раз.')
        bot.register_next_step_handler(msg, password_check)


def get_information_about_person(message: Message):
    full_name = message.text

    if len(full_name.split()) < 3:
        bot.send_message(message.from_user.id,
                         'Неправильный формат ввода. Обратите внимание на то, что нужно ввести Фамилию Имя Отчество. Попробуйте ввести ещё раз.')
        bot.register_next_step_handler(message, get_information_about_person)
    else:
        people[message.from_user.id] = Person()
        people[message.from_user.id].full_name = full_name
        # PEOPLE[message.from_user.id].tg_id = message.from_user.id
        profession_markup = InlineKeyboardMarkup()

        with db_session.create_session() as db:

            for prof in db.scalars(select(users.PersonGroup)):
                profession_markup.add(InlineKeyboardButton(prof.name, callback_data='group_' + str(prof.id)))
            profession_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
            bot.send_message(message.from_user.id, 'Выбери группы, к которым ты относишься',
                             reply_markup=profession_markup)


def add_new_person(call: CallbackQuery):
    telegram_id = call.from_user.id
    people[telegram_id].tg_id = telegram_id
    with db_session.create_session() as db:
        db.add(people[telegram_id])
        db.commit()
        bot.send_message(call.message.chat.id,
                         'Опрос пройден успешно. Теперь каждый день тебе будут присылаться тестовые вопросы, на которые '
                         'нужно отвечать) Желаю удачи.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('group'))
def select_groups(call: CallbackQuery):
    with db_session.create_session() as db:

        group_id = int(call.data.split('_')[1])
        groups = db.scalars(select(users.PersonGroup))
        person = people[call.from_user.id]
        current_group = db.scalars(select(users.PersonGroup).where(users.PersonGroup.id == group_id)).first()

        if current_group.id not in [group.id for group in person.groups]:
            person.groups.append(current_group)
        else:
            person.groups.remove([group for group in person.groups if group.id == group_id][0])
        groups_markup = InlineKeyboardMarkup()

        for prof in groups:
            if prof.id in [i.id for i in person.groups]:
                groups_markup.add(InlineKeyboardButton(prof.name + "\U00002713", callback_data='group_' + str(prof.id)))
            else:
                groups_markup.add(InlineKeyboardButton(prof.name, callback_data='group_' + str(prof.id)))

        groups_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=groups_markup)


# первыйй ответ дня, пять правильых ответов подряд ачивкки

def send_question(person: Person, pending_question: Question):
    markup = InlineKeyboardMarkup()
    options = json.loads(pending_question.options)
    question_text = pending_question.text
    buttons = []
    for answer_index in range(len(options)):
        question_text += '\n' + str(answer_index + 1) + '. ' + options[answer_index]
        buttons.append(InlineKeyboardButton(answer_index + 1, callback_data='answer_' + str(answer_index + 1)))
    markup.add(*buttons, InlineKeyboardButton('Не знаю:(', callback_data='answer_0', ), row_width=len(buttons))
    question[person.tg_id] = pending_question
    bot.send_message(person.tg_id, question_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('answer'))
def check_answer(call: CallbackQuery):
    with db_session.create_session() as db:
        merged_question = db.merge(question[call.from_user.id])

        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        if call.data.split('_')[1] == str(merged_question.answer):
            bot.send_message(call.from_user.id, 'Юхуууу, правильный ответ, на тебе котика')
            bot.send_sticker(call.message.chat.id,
                             'CAACAgIAAxkBAAKNcWS5VJzS8g3EFokDZRtF_6HdZeCWAALDEQACBAfQSWPVxMPrmkD0LwQ')
        else:
            if merged_question.article_url:
                bot.send_message(call.from_user.id,
                                 'Как жаль, ответ неправильный. Правильный ответ - '
                                 + str(merged_question.answer)
                                 + '. Вот тебе интересная статья по этой теме.'
                                 + '\n' + merged_question.article_url)
            else:
                bot.send_message(call.from_user.id, 'Увы, ответ неправильный, не грустите, вот вам котик. '
                                                    'Правильный ответ ' + str(merged_question.answer))
                bot.send_sticker(call.from_user.id,
                                 'CAACAgIAAxkBAAKPKGS6egABoGGgMSoZw0FbL4DCE463GgACIxQAAuY5aUuwlIfNRnd6pi8E')

        question_id = merged_question.id
        person_answer = int(call.data.split('_')[1])
        person_id = db.scalar(select(users.Person).where(users.Person.tg_id == call.from_user.id)).id
        planned_question = db.scalar(select(questions.QuestionAnswer).where(
            questions.QuestionAnswer.person_id == person_id).where(
            questions.QuestionAnswer.question_id == question_id).where(
            questions.QuestionAnswer.state == questions.AnswerState.TRANSFERRED))
        if planned_question is not None:
            planned_question.person_answer = person_answer
            planned_question.state = questions.AnswerState.ANSWERED
            planned_question.answer_time = datetime.datetime.now()
            db.commit()


def start_bot():
    def poller():
        bot.polling(none_stop=True)

    bot_th = Thread(target=poller, daemon=True)
    bot_th.start()
    return bot
