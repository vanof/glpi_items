import telebot
import os
import message_handler
from dotenv import load_dotenv
from telebot import types

load_dotenv('env.env')

# Initialize the Telegram bot
bot = telebot.TeleBot(os.getenv("BOT_ID"))

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = types.KeyboardButton("Получить характеристики ПК")
button2 = types.KeyboardButton("Сгенерировать QR")
keyboard.add(button1, button2)


@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне сообщение, которое нужно передать в GLPI  или выбери действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    input_message = message.text

    message_handler.input_message_1 = input_message
    message_handler.go()
    bot.reply_to(message, "Сообщение передано в GLPI.")
    print(message_handler.input)
    bot.send_message(message.chat.id, "Отправь мне сообщение, которое нужно передать в GLPI или выбери действие:", reply_markup=keyboard)


if __name__ == "__main__":
    bot.polling()
