import os
from threading import Thread
from models import db_session, users

import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, ReplyKeyboardMarkup, \
    KeyboardButton

print(os.environ['TGTOKEN'])
bot = telebot.TeleBot(os.environ['TGTOKEN'])
GROUPS = ['programmer', 'designer', 'director']
PEOPLE = dict()


@bot.message_handler(commands=["start"])
def start_handler(message):
    start_markup = InlineKeyboardMarkup()
    start_markup.add(InlineKeyboardButton(text='Начать', callback_data='is_started'))
    bot.send_message(message.from_user.id,
                     'Привет, я бот для тестирования сотрудников 3divi. Перед началом тебе нужно ответить на пару вопросов.',
                     reply_markup=start_markup)


@bot.callback_query_handler(func=lambda call: call.data in GROUPS)
def select_groups(call: CallbackQuery):
    if GROUPS.index(call.data) not in PEOPLE[call.from_user.id]:
        PEOPLE[call.from_user.id].append(GROUPS.index(call.data))
        group_markup = InlineKeyboardMarkup()
        for prof in GROUPS:
            if prof == call.data or GROUPS.index(prof) in PEOPLE[call.from_user.id]:
                group_markup.add(InlineKeyboardButton(prof + '✔️', callback_data=prof))
            else:
                group_markup.add(InlineKeyboardButton(prof, callback_data=prof))
    else:
        PEOPLE[call.from_user.id].remove(GROUPS.index(call.data))
        group_markup = InlineKeyboardMarkup()
        for prof in GROUPS:
            if GROUPS.index(prof) in PEOPLE[call.from_user.id]:
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

        for prof in GROUPS:
            profession_markup.add(InlineKeyboardButton(prof, callback_data=prof))
        profession_markup.add(InlineKeyboardButton('Завершить', callback_data='end_of_register'))
        msg = bot.send_message(message.from_user.id, 'Выбери группы, к которым ты относишься',
                               reply_markup=profession_markup)


def add_new_person(call: CallbackQuery):
    telegram_id = call.from_user.id
    db = db_session.create_session()
    person = users.Person()
    person.full_name = PEOPLE[telegram_id][0]
    person.tg_id = telegram_id
    # print(PEOPLE[telegram_id])
    for i in range(1, len(PEOPLE[telegram_id])):
        print(PEOPLE[telegram_id][i])
        person.groups.append(PEOPLE[telegram_id][i])
    db.add(person)
    db.commit()
    bot.send_message(call.message.chat.id,
                     'Опрос пройден успешно. Теперь каждый день тебе будут присылаться тестовые вопросы, на которые нужно отвечать) Желаю удачи.')


def send_question(question: [], telegram_id):
    answer_markup = ReplyKeyboardMarkup()
    for i in range(1, 5):
        answer_markup.add(KeyboardButton(str(i)))
    answer_markup.add(KeyboardButton('Не знаю'))
    bot.send_message(telegram_id,
                     question[0] + '\n' + question[1] + '\n' + question[2] + '\n' + question[3] + '\n' + question[4],
                     reply_markup=answer_markup)


def start_bot():
    def poller():
        bot.polling(none_stop=True)

    bot_th = Thread(target=poller, daemon=True)
    bot_th.start()
    return bot
