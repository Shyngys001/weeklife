import os
import sqlite3
from datetime import datetime
from random import choice
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from life_chart import generate_high_quality_life_chart

# Настройки
TOKEN = "7784577846:AAGOSVUBf6J33PFSZo9ApK8NGSS4XU0Cv1w"
DB_PATH = "users.db"
PORT = int(os.environ.get("PORT", 8443))
URL = os.environ.get("RENDER_EXTERNAL_URL")

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

MOTIVATIONAL_QUOTES = [
    "Живи осознанно 🙏",
    "Каждая неделя – новый шанс! ⚡",
    "Время – твой самый ценный ресурс ⏳",
    "Твой прогресс вдохновляет! 🚀",
]

# Твоя логика — без изменений
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            birth_date TEXT
        )
    ''')
    c.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in c.fetchall()]
    if "is_subscribed" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN is_subscribed INTEGER DEFAULT 0")
    conn.commit()
    conn.close()

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📈 Мой прогресс", callback_data="progress"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔗 Поделиться", callback_data="share"),
         InlineKeyboardButton("💎 Подписка", callback_data="subscribe")],
        [InlineKeyboardButton("⚡ Быстрые команды", callback_data="quick")]
    ]
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Отправь дату рождения (ДД.ММ.ГГГГ), и я покажу тебе таблицу жизни!",
        reply_markup=get_main_menu()
    )

def handle_birthdate(update: Update, context: CallbackContext):
    try:
        birth_date = datetime.strptime(update.message.text, "%d.%m.%Y")
        user_id = update.message.from_user.id
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO users (user_id, birth_date, is_subscribed) VALUES (?, ?, COALESCE((SELECT is_subscribed FROM users WHERE user_id = ?), 0))",
                  (user_id, birth_date.strftime("%d.%m.%Y"), user_id))
        conn.commit()
        conn.close()

        image_path, weeks = generate_high_quality_life_chart(birth_date.strftime("%d.%m.%Y"))
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_path, 'rb'))
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ты прожил свою {weeks} неделю. {choice(MOTIVATIONAL_QUOTES)}", reply_markup=get_main_menu())
    except ValueError:
        update.message.reply_text("Неверный формат. Используй ДД.ММ.ГГГГ.")

def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT birth_date, is_subscribed FROM users WHERE user_id = ?", (query.from_user.id,))
    result = c.fetchone()
    conn.close()

    if not result:
        query.edit_message_text("Сначала отправь свою дату рождения!")
        return

    birth_date, is_subscribed = result

    if data == "progress":
        image_path, weeks = generate_high_quality_life_chart(birth_date)
        context.bot.send_photo(chat_id=query.from_user.id, photo=open(image_path, 'rb'))
        query.edit_message_text(f"Ты прожил свою {weeks} неделю. {choice(MOTIVATIONAL_QUOTES)}", reply_markup=get_main_menu())
    elif data == "stats":
        total_weeks = 52 * 70
        image_path, weeks = generate_high_quality_life_chart(birth_date)
        percent = (weeks / total_weeks) * 100
        remaining = total_weeks - weeks
        query.edit_message_text(f"Общая продолжительность жизни: {total_weeks} недель.\nПрожито: {weeks} недель ({percent:.2f}%).\nОсталось: {remaining} недель.", reply_markup=get_main_menu())
    elif data == "share":
        query.edit_message_text("Я использую @weeklife1_bot, чтобы отслеживать свой прогресс! Присоединяйся: @weekbot1", reply_markup=get_main_menu())
    elif data == "subscribe":
        if is_subscribed:
            query.edit_message_text("Вы уже подписаны!", reply_markup=get_main_menu())
        else:
            query.edit_message_text("Подпишитесь на наш канал и поддержите @weekbot1. Следи за новостями!", reply_markup=get_main_menu())
    elif data == "quick":
        query.edit_message_text("/start — перезапуск\nОтправь дату рождения ДД.ММ.ГГГГ", reply_markup=get_main_menu())
    else:
        query.edit_message_text("Неизвестная команда.", reply_markup=get_main_menu())

# Обработчики
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_birthdate))
dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "LifeWeeksBot работает!"

# Запуск приложения
if __name__ == '__main__':
    init_db()
    bot.set_webhook(f"{URL}{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)