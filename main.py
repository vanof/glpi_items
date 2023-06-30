import telebot
import os
import message_handler
import logging
from dotenv import load_dotenv
from telebot import types

load_dotenv('env.env')

# Initialize the Telegram bot
bot = telebot.TeleBot(os.getenv("BOT_ID"))

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = types.KeyboardButton("Получить характеристики ПК")
button2 = types.KeyboardButton("Сгенерировать QR")
keyboard.add(button1, button2)


logging.basicConfig(
    filename='log_file.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне сообщение, которое нужно передать в GLPI или выбери действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Получить характеристики ПК":
        bot.send_message(message.chat.id, "Вы выбрали получение характеристик")
        bot.send_message(message.chat.id, "Отправь мне сообщение, которое нужно передать в GLPI или выбери действие:",
                         reply_markup=keyboard)

    elif message.text == "Сгенерировать QR":
        bot.send_message(message.chat.id, "Вы выбрали генерацию QR")
        bot.send_message(message.chat.id, "Отправь мне сообщение, которое нужно передать в GLPI или выбери действие:",
                         reply_markup=keyboard)

    else:
        message_handler.message_handler(message.text)
        bot.reply_to(message, "Сообщение передано в GLPI.")
        bot.send_message(message.chat.id, "Отправь мне сообщение, которое нужно передать в GLPI или выбери действие:", reply_markup=keyboard)


if __name__ == "__main__":
    bot.polling()
