import pandas as pd
import sqlite3

db = sqlite3.connect("telegram_messages.db")

df = pd.read_sql_query("SELECT * FROM messages", db)


df['label'] = df['label'].fillna(0)
df.loc[df['proceeded_text'].str.contains("концерт|билет"), 'label'] = 1

df.to_sql('messages', db, if_exists='replace', index=False)

db.close()

