from secret import SECRETEAPI, APP_API_HASH, APP_ID_HASH, CHANNELS_NAMES_TO_PARSE
from one_time_parse import prepare_text_for_tf_idf
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo
from telebot.types import InputMediaPhoto, InputMediaVideo
from telethon.extensions import html
import telebot, asyncio, threading, joblib, io

TIME_TO_FREEZE = 0.1
MAX_MB = 20 * 1024 * 1024
pipeline = joblib.load("model_pipeline.pkl")
bot = telebot.TeleBot(SECRETEAPI)
subscribers = set([1128560375])
client = TelegramClient("bot_parser", APP_ID_HASH, APP_API_HASH)


def is_politics(text):
    return pipeline.predict([prepare_text_for_tf_idf(text)])[0]

def check_message(message):
    if not message:
        return False
    return is_politics(message)    

def check_for_video(attrs):
    return any(isinstance(attr, DocumentAttributeVideo) for attr in attrs)


@client.on(events.Album(chats=CHANNELS_NAMES_TO_PARSE))
async def album_handler(event):

    raw_text = (event.messages[0].raw_text or "") if event.messages else ""
    if check_message(raw_text):
        return
    

    first_msg = event.messages[0]
    caption_html = html.unparse(first_msg.message, first_msg.entities) if first_msg.message else ""
    
    media_group = []
    for i, msg in enumerate(event.messages):
        if msg.file and msg.file.size > MAX_MB:
            return
        file_data = await client.download_media(msg.media, file=io.BytesIO())
        if isinstance(msg.media, MessageMediaPhoto):
            file_data.name = f"photo_{i}.jpg"
            media_group.append(InputMediaPhoto(file_data, caption=caption_html if i == 0 else "", parse_mode='HTML'))
        
        elif isinstance(msg.media, MessageMediaDocument):
            is_video = check_for_video(msg.media.document.attributes)
            if is_video:
                file_data.name = f"video_{i}.mp4"
                media_group.append(InputMediaVideo(file_data, caption=caption_html if i == 0 else "", parse_mode='HTML'))
        
    if media_group:
        for user_id in list(subscribers):
            try:
                await asyncio.sleep(TIME_TO_FREEZE)
                for m in media_group:
                    m.media.seek(0)
                bot.send_media_group(user_id, media_group)
            except Exception as e:
                print(f"Ошибка альбома для {user_id}: {e}")

@client.on(events.NewMessage(chats=CHANNELS_NAMES_TO_PARSE))
async def handler(event):
    message = event.message
    if event.grouped_id:
        return
    
    if check_message(message.raw_text or ''):
        return
    
    text_html = html.unparse(message.message, message.entities) if message.message else ""
    
    file_data = None
    if message.media:
        if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
            if message.file and message.file.size > MAX_MB:
                return
            file_data = await client.download_media(message.media, file=io.BytesIO())
            if isinstance(message.media, MessageMediaDocument):
                file_data.name = "file.dat"
                for attr in message.media.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_data.name = attr.file_name

    for user_id in list(subscribers):
        try:
            await asyncio.sleep(TIME_TO_FREEZE)
            if file_data:
                file_data.seek(0)
                if isinstance(message.media, MessageMediaPhoto):
                    bot.send_photo(user_id, photo=file_data, caption=text_html, parse_mode='HTML')
                elif isinstance(message.media, MessageMediaDocument):
                    is_video = check_for_video(message.media.document.attributes)
                    if is_video:
                        bot.send_video(user_id, video=file_data, caption=text_html, parse_mode='HTML')
                    else:
                        bot.send_document(user_id, document=file_data, caption=text_html, parse_mode='HTML')
            else:
                bot.send_message(user_id, text_html, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка сообщения для {user_id}: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я присылаю новости без политики.\nНапиши /on чтобы получить сообщения в реальном времени из тг каналов и /off чтобы выключить.")

@bot.message_handler(commands=['on'])
def turn_on(message):
    subscribers.add(message.chat.id)
    bot.send_message(message.chat.id, "✅ Подписка включена")

@bot.message_handler(commands=['off'])
def turn_off(message):
    subscribers.discard(message.chat.id)
    bot.send_message(message.chat.id, "❌ Подписка выключена")



async def start_client():
    await client.start()
    await client.run_until_disconnected()


def start_parser():
    asyncio.run(start_client())

threading.Thread(target=start_parser, daemon=True).start()

bot.polling(none_stop=True, interval=0)