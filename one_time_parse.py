import asyncio, pymorphy3, sqlite3, re, emoji
from nltk.corpus import stopwords
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from secret import APP_API_HASH, APP_ID_HASH, DAYS_TO_PARSE

channel_username = 'superdiscoclub'
morph = pymorphy3.MorphAnalyzer()
stop_words = set(stopwords.words("russian"))
client = TelegramClient('parser_session', APP_ID_HASH, APP_API_HASH)

#создание таблицы
conn = sqlite3.connect("telegram_messages.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    channel TEXT,
    message_id INTEGER,
    raw_text TEXT,
    proceeded_text TEXT,
    label BOOL,
    PRIMARY KEY(channel, message_id)
)
""")

conn.commit()

#подготовка данных
def prepare_text_for_tf_idf(text: str):
    text = text.lower()
    text = emoji.replace_emoji(text, '')
    text = re.sub(r"http\S+", '', text)
    text = re.sub(r"[@#]\w+", '', text)
    text = re.sub(r"[^\w\s]", '', text)
    words = text.split()
    words = [w for w in words if w not in stop_words and not w.isdigit()]
    words = [morph.parse(w)[0].normal_form for w in words]

    return " ".join(words)


async def main():
    async with client:
        #находим сообщение с которого будем парсить канал
        cursor.execute("SELECT EXISTS(SELECT 1 FROM messages WHERE channel = ?)", (channel_username,))
        exists = cursor.fetchone()[0]
        offset_date = datetime.now(timezone.utc) - timedelta(days=DAYS_TO_PARSE)
        get_messages = client.iter_messages(channel_username, offset_date=offset_date, reverse=True)
        if exists:
            cursor.execute("""
                            SELECT MAX(message_id)
                            FROM messages
                            WHERE channel = ?
                        """, 
                        (channel_username,)
                        )
            last_id = cursor.fetchone()[0]
            get_messages = client.iter_messages(channel_username, offset_id=last_id, reverse=True)
            print(f"Начинаю поиск сообщений старше: {last_id}")
        else:
            print(f"Начинаю поиск сообщений старше: {offset_date}")

        #парсим
        async for message in get_messages:
            if message.text:
                cursor.execute("""
                            INSERT or IGNORE INTO messages (channel, message_id, raw_text, proceeded_text)
                            VALUES (?, ?, ?, ?)
                """, (
                    channel_username,
                    message.id,
                    message.text,
                    prepare_text_for_tf_idf(message.text)
                ))
    conn.commit()

asyncio.run(main())