from secret import SECRETEAPI, APP_API_HASH, APP_ID_HASH, CHANNELS_NAMES_TO_PARSE
from one_time_parse import prepare_text_for_tf_idf
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo
from telebot.types import InputMediaPhoto, InputMediaVideo
from telethon.extensions import html
from telebot.async_telebot import AsyncTeleBot
import asyncio, threading, joblib, io, aiosqlite

TIME_TO_FREEZE = 0.1
MAX_MB = 20 * 1024 * 1024
DB_PATH = 'bot_data.db'
pipeline = joblib.load("model_pipeline.pkl")
bot = AsyncTeleBot(SECRETEAPI)
client = TelegramClient("bot_parser", APP_ID_HASH, APP_API_HASH)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS subs (user_id INTEGER PRIMARY KEY)')
        await db.commit()

async def add_sub(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO subs (user_id) VALUES (?)', (user_id,))
        await db.commit()


async def remove_sub(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM subs WHERE user_id = ?', (user_id,))
        await db.commit()


async def get_subs():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT user_id FROM subs') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


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
        subscribers = await get_subs()
        for user_id in subscribers:
            try:
                await asyncio.sleep(TIME_TO_FREEZE)
                for m in media_group:
                    m.media.seek(0)
                await bot.send_media_group(user_id, media_group)
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
    subscribers = await get_subs()
    for user_id in subscribers:
        try:
            await asyncio.sleep(TIME_TO_FREEZE)
            if file_data:
                file_data.seek(0)
                if isinstance(message.media, MessageMediaPhoto):
                    await bot.send_photo(user_id, photo=file_data, caption=text_html, parse_mode='HTML')
                elif isinstance(message.media, MessageMediaDocument):
                    is_video = check_for_video(message.media.document.attributes)
                    if is_video:
                        await bot.send_video(user_id, video=file_data, caption=text_html, parse_mode='HTML')
                    else:
                        await bot.send_document(user_id, document=file_data, caption=text_html, parse_mode='HTML')
            else:
                await bot.send_message(user_id, text_html, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка сообщения для {user_id}: {e}")


@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, "Привет! Я присылаю новости без политики.\nНапиши /on чтобы получить сообщения в реальном времени из тг каналов и /off чтобы выключить.")

@bot.message_handler(commands=['on'])
async def turn_on(message):
    await add_sub(message.chat.id)
    await bot.send_message(message.chat.id, "✅ Подписка включена")

@bot.message_handler(commands=['off'])
async def turn_off(message):
    await remove_sub(message.chat.id)
    await bot.send_message(message.chat.id, "❌ Подписка выключена")


async def main():
    await init_db()
    await client.start()
    await asyncio.gather(
        client.run_until_disconnected(),
        bot.polling(none_stop=True)
    )

if __name__ == '__main__':
    asyncio.run(main())