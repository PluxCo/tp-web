import os
from threading import Thread

from sqlalchemy import select

from models import db_session
from models import users, questions
from web.forms.users import LoginForm, UserCork, CreateGroupForm
from web.forms.questions import CreateQuestionForm
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, ReplyKeyboardMarkup, \
    KeyboardButton

print(os.environ['TGTOKEN'])
bot = telebot.TeleBot(os.environ['TGTOKEN'])
PEOPLE = dict()


@bot.message_handler(commands=["start"])
def start_handler(message):
    start_markup = InlineKeyboardMarkup()
    start_markup.add(InlineKeyboardButton(text='Начать', callback_data='is_started'))
    bot.send_message(message.from_user.id,
                     'Привет, я бот для тестирования сотрудников 3divi. Перед началом тебе нужно ответить на пару вопросов.',
                     reply_markup=start_markup)


def get_groups_from_db():
    db = db_session.create_session()

    groups = [item.name for item in db.scalars(select(users.PersonGroup))]
    return groups


@bot.callback_query_handler(func=lambda call: call.data in get_groups_from_db())
def select_groups(call: CallbackQuery):
    groups = get_groups_from_db()
    group_index = groups.index(call.data) + 1
    person_id = call.from_user.id

    if group_index not in PEOPLE[person_id]:
        PEOPLE[person_id].append(group_index)
        group_markup = InlineKeyboardMarkup()
    else:
        PEOPLE[person_id].remove(group_index)
        group_markup = InlineKeyboardMarkup()

    for prof in groups:
        if prof == call.data or groups.index(prof) + 1 in PEOPLE[person_id]:
            group_markup.add(InlineKeyboardButton(prof + '✔️', callback_data=prof))
        else:
            group_markup.add(InlineKeyboardButton(prof, callback_data=prof))

    group_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=group_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    if call.data == "is_started":
        message = bot.send_message(call.message.chat.id, 'Введите код доступа')
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        bot.register_next_step_handler(message, password_check)
    if call.data == 'end_of_register':
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)
        add_new_person(call)


@bot.message_handler()
def password_check(message):
    if message.text == os.environ['PASSWORD']:
        msg = bot.send_message(message.chat.id, 'Как тебя зовут(ФИО)?')
        bot.register_next_step_handler(msg, get_information_about_person)
    else:
        msg = bot.send_message(message.chat.id, 'Неверный код доступа. Попробуйте ещё раз.')
        bot.register_next_step_handler(msg, password_check)


@bot.message_handler()
def get_information_about_person(message):
    full_name = message.text
    if len(full_name.split()) < 3:
        bot.send_message(message.from_user.id,
                         'Неправильный формат ввода. Обратите внимание на то, что нужно ввести Фамилию Имя Отчество. Попробуйте ввести ещё раз.')
        bot.register_next_step_handler(message, get_information_about_person)
    else:
        PEOPLE[message.from_user.id] = [full_name]
        profession_markup = InlineKeyboardMarkup()

        groups = get_groups_from_db()
        print(groups)

        for prof in groups:
            profession_markup.add(InlineKeyboardButton(prof, callback_data=prof))
        profession_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
        bot.send_message(message.from_user.id, 'Выбери группы, к которым ты относишься',
                         reply_markup=profession_markup)


def add_new_person(call: CallbackQuery):
    telegram_id = call.from_user.id
    db = db_session.create_session()
    person = users.Person()
    person.full_name = PEOPLE[telegram_id][0]
    person.tg_id = telegram_id
    # print(PEOPLE[telegram_id])
    db = db_session.create_session()
    # groups = [(str(item.id), item.name) for item in db.scalars(select(users.PersonGroup))]
    # create_question_form.groups.choices = groups
    selected_groups = db.scalars(select(users.PersonGroup).where(users.PersonGroup.id.in_(PEOPLE[telegram_id][1:])))
    person.groups.extend(selected_groups)
    db.add(person)
    db.commit()
    bot.send_message(call.message.chat.id,
                     'Опрос пройден успешно. Теперь каждый день тебе будут присылаться тестовые вопросы, на которые нужно отвечать) Желаю удачи.')


def send_question(question: [], telegram_id):
    answer_markup = InlineKeyboardMarkup()
    for i in range(1, 5):
        if i - 1 == question[5]:
            answer_markup.add(InlineKeyboardButton(question[i], callback_data='right_answer'))
        else:
            answer_markup.add(InlineKeyboardButton(question[i], callback_data='wrong_answer'))
    answer_markup.add(InlineKeyboardButton('Не знаю', callback_data='dont_know'))
    bot.send_message(telegram_id, question[0], reply_markup=answer_markup)


@bot.callback_query_handler(func=lambda call: call.data in ['right_answer', 'wrong_answer', 'dont_know'])
def check_answer(call: CallbackQuery):
    if call.data == 'right_answer':
        bot.send_message(call.message.chat.id, 'Юхуу, поздравляю, это правильный ответ.')
    elif call.data == 'dont_know':
        bot.send_message(call.message.chat.id, 'Как жаль.. Нужно немного почитать на эту тему')
    else:
        bot.send_message(call.message.chat.id, 'Увы, это неправильный ответ:(' + '\n' + ' Надеюсь, что в следующий раз вы не ошибётесь')
    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=None)


def start_bot():
    def poller():
        bot.polling(none_stop=True)

    bot_th = Thread(target=poller, daemon=True)
    bot_th.start()
    return bot
