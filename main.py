import os
import sqlite3
from datetime import datetime
from random import choice
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackContext, 
                          CallbackQueryHandler)
from life_chart import generate_high_quality_life_chart

# Замените на свой токен, полученный у @BotFather
TOKEN = "7784577846:AAGOSVUBf6J33PFSZo9ApK8NGSS4XU0Cv1w"
DB_PATH = "users.db"

MOTIVATIONAL_QUOTES = [
    "Живи осознанно 🙏",
    "Каждая неделя – новый шанс! ⚡",
    "Время – твой самый ценный ресурс ⏳",
    "Твой прогресс вдохновляет! 🚀",
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            birth_date TEXT
        )
    ''')
    conn.commit()
    # Добавляем столбец is_subscribed, если его нет
    c.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in c.fetchall()]
    if "is_subscribed" not in columns:
        try:
            c.execute("ALTER TABLE users ADD COLUMN is_subscribed INTEGER DEFAULT 0")
            conn.commit()
        except Exception as e:
            print("Ошибка при добавлении столбца is_subscribed:", e)
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
        "Привет!\nОтправь мне свою дату рождения в формате ДД.ММ.ГГГГ, и я покажу тебе таблицу жизни!",
        reply_markup=get_main_menu()
    )

def handle_birthdate(update: Update, context: CallbackContext):
    try:
        birth_date = datetime.strptime(update.message.text, "%d.%m.%Y")
        user_id = update.message.from_user.id

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "REPLACE INTO users (user_id, birth_date, is_subscribed) VALUES (?, ?, COALESCE((SELECT is_subscribed FROM users WHERE user_id = ?), 0))",
            (user_id, birth_date.strftime("%d.%m.%Y"), user_id)
        )
        conn.commit()
        conn.close()

        image_path, weeks = generate_high_quality_life_chart(birth_date.strftime("%d.%m.%Y"))
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(image_path, 'rb'))
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ты прожил свою {weeks} неделю. {choice(MOTIVATIONAL_QUOTES)}",
            reply_markup=get_main_menu()
        )
    except ValueError:
        update.message.reply_text("Неверный формат. Используй, пожалуйста, ДД.ММ.ГГГГ.")

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
        query.edit_message_text(
            f"Ты прожил свою {weeks} неделю. {choice(MOTIVATIONAL_QUOTES)}",
            reply_markup=get_main_menu()
        )
    elif data == "stats":
        total_weeks = 52 * 70
        image_path, weeks = generate_high_quality_life_chart(birth_date)
        percent = (weeks / total_weeks) * 100
        remaining = total_weeks - weeks
        stats_text = (f"Общая продолжительность жизни: {total_weeks} недель.\n"
                      f"Прожито: {weeks} недель ({percent:.2f}%).\n"
                      f"Осталось: {remaining} недель.")
        query.edit_message_text(stats_text, reply_markup=get_main_menu())
    elif data == "share":
        share_text = "Я использую @weeklife1_bot, чтобы отслеживать свой прогресс! Присоединяйся: @weekbot1"
        query.edit_message_text(share_text, reply_markup=get_main_menu())
    elif data == "subscribe":
        if is_subscribed:
            query.edit_message_text("Вы уже подписаны на премиум-функции!", reply_markup=get_main_menu())
        else:
            query.edit_message_text("Подпишитесь на наш канал и поддержите @weekbot1. Следи за новостями!", reply_markup=get_main_menu())
    elif data == "quick":
        quick_text = ("Быстрые команды:\n"
                      "/start - Перезапустить бота\n"
                      "Отправь дату рождения в формате ДД.ММ.ГГГГ для обновления таблицы.")
        query.edit_message_text(quick_text, reply_markup=get_main_menu())
    else:
        query.edit_message_text("Неизвестная команда.", reply_markup=get_main_menu())

def send_weekly_updates(context: CallbackContext):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, birth_date FROM users")
    users = c.fetchall()
    conn.close()

    for user_id, birth_date in users:
        try:
            image_path, weeks = generate_high_quality_life_chart(birth_date)
            context.bot.send_photo(chat_id=user_id, photo=open(image_path, 'rb'))
            context.bot.send_message(
                chat_id=user_id,
                text=f"Еженедельное обновление:\nТы прожил свою {weeks} неделю. {choice(MOTIVATIONAL_QUOTES)}",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")
            continue

def main():
    init_db()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    jq = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_birthdate))
    dp.add_handler(CallbackQueryHandler(handle_callback_query))

    # Рассылка каждую неделю (604800 секунд), первая отправка через 10 секунд (для теста)
    jq.run_repeating(send_weekly_updates, interval=604800, first=10)

    updater.start_polling()
    updater.idle()

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "LifeWeeksBot работает!"

if __name__ == '__main__':
    from telegram.ext import Updater
    init_db()
    bot.set_webhook(url=f"{URL}{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)