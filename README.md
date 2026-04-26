# 📰 Telegram News Filter Bot

Бот, который собирает новости из Telegram-каналов и отправляет пользователю только те, которые **не связаны с политикой**

## 🚀 Возможности

* 📡 Сканирует Telegram-каналы в реальном времени
* 🧠 Фильтрует сообщения с помощью ML-модели (TF-IDF + Logistic Regression)
* 🔴 Режим реального времени (/on)
* 🔁 Пересылка отфильтрованных сообщений

---

## 🧠 Модель

Используется:

* TF-IDF векторизация
* Logistic Regression

Модель обучена на размеченных Telegram-сообщениях (политика / не политика).

---

## ⚙️ Установка

```bash
git clone https://github.com/oleg456-g/News_Telegram_Bot.git
cd News_Telegram_Bot
pip install -r requirements.txt
```
Затем откройте Python консоль и введите две команды:
```bash
import nltk
nltk.download()
```
Кликните download в открывшемся окне
---

## 🔑 Настройка

Создай файл `secret.py` по подобию secret.py.example:

```python
SECRETEAPI - API твоего бота в Telegram
Как получить?
BotFather в Telegram

APP_ID_HASH, APP_API_HASH - ID и API_HASH твоего Telegram
Как получить?
https://docs.telethon.dev/en/stable/basic/signing-in.html

CHANNELS_NAMES_TO_PARSE - названия телеграмм каналов, которые ты хочешь мониторить
```

---

## ▶️ Запуск

```bash
python main.py
```

---

## 🤖 Команды бота

* `/start` — описание
* `/on` — включить realtime
* `/off` — выключить

---

## ⚠️ Важно

* На аккаунте Telegram, с которого подключен Telethon, должны быть в списке подписок каналы из CHANNELS_NAMES_TO_PARSE
* При большом потоке возможны ограничения Telegram API

---

## 🚀 Планы по улучшению

* [ ] Переход на BERT
* [ ] Веб-интерфейс
