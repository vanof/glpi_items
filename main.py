import telebot
from telebot import types

import os
import message
from dotenv import load_dotenv

load_dotenv('env.env')

# Initialize the Telegram bot
bot = telebot.TeleBot(os.getenv("BOT_ID"))


# Обработчик команды "/start"
@bot.message_handler(commands=["start"])
def handle_start(message):
    # Отправить приветственное сообщение
    bot.send_message(message.chat.id, "Привет! Отправь мне сообщение, которое нужно передать в message.py")

    # Создать клавиатуру с двумя кнопками
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    button1 = types.KeyboardButton("Получить характеристики ПК")
    button2 = types.KeyboardButton("Сгенерировать QR")
    keyboard.add(button1, button2)

    # Отправить клавиатуру пользователю
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=keyboard)


# Обработчик всех входящих сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Получить текст сообщения
    input_message = message.text

    # Установить значение переменной input в модуле message
    message.input = input_message

    # Отправить подтверждение
    bot.reply_to(message, "Сообщение передано в message.py")


if __name__ == "__main__":
    bot.polling()
