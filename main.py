from secret import SECRETEAPI
import telebot
bot = telebot.TeleBot(SECRETEAPI)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, "Лучший Telegram бот для получения новостей без политики и т.п.")
bot.polling(none_stop=True, interval=0)
