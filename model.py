from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import pandas as pd
import sqlite3
import joblib

conn = sqlite3.connect("telegram_messages.db")
data = pd.read_sql_query("SELECT proceeded_text, label FROM messages WHERE label IS NOT NULL", conn)
conn.close()


X_train, X_test, Y_train, Y_test = train_test_split(data['proceeded_text'], data['label'], test_size=0.2, random_state=52)
pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(
                                            max_features=10000,
                                            ngram_range=(1,2),
                                            stop_words=None,
                                        )),
                ('logreg', LogisticRegression(
                                            max_iter=1000000,   
                                            class_weight='balanced',
                                            C=7,
                                        )),
            ])

pipeline.fit(X_train, Y_train)
joblib.dump(pipeline, "model_pipeline.pkl")
