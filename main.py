from secret import SECRETEAPI
import telebot
bot = telebot.TeleBot(SECRETEAPI)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, "Хей бро, где хочешь зачиллить сегодня?")
bot.polling(none_stop=True,interval=0)
