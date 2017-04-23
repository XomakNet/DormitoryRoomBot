import telebot

from config import TELEGRAM_TOKEN
from core.db import init_database
from core.sessions import SessionsController

__author__ = 'Xomak'

init_database()


bot = telebot.TeleBot(TELEGRAM_TOKEN)
sessions = SessionsController(bot)


@bot.message_handler(content_types=['text'])
def send_something(message):
    sessions.get_session_by_chat_id(message.chat.id).handle_message(message)


bot.polling()