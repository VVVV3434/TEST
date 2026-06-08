import os
import re
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
FUNPAY_URL = os.getenv("FUNPAY_URL")

SECRET_CODE = "5555"

MIN_PRICE = 100
MAX_PRICE = 200

found_count = 0

web_app = Flask(__name__)


@web_app.get("/")
def home():
    return "Bot is running"


def run_web():
    port = int(os.getenv("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


def convert_to_rubles(price_text):
    text = price_text.lower().replace(",", ".")

    number_match = re.search(r"\d+(\.\d+)?", text)
    if not number_match:
        return None

    price = float(number_match.group())

    if "₽" in text or "руб" in text:
        return price

    if "$" in text or "usd" in text:
        return price * 90  # примерный курс

    if "€" in text or "eur" in text:
        return price * 100  # примерный курс

    return None


def parse_funpay():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(FUNPAY_URL, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    count = 0

    offers = soup.find_all("a", href=True)

    for offer in offers:
        text = offer.get_text(" ", strip=True)

        if not text:
            continue

        rub_price = convert_to_rubles(text)

        if rub_price is None:
            continue

        if MIN_PRICE <= rub_price <= MAX_PRICE:
            count += 1

    return count


async def check_funpay(context: ContextTypes.DEFAULT_TYPE):
    global found_count

    try:
        found_count = parse_funpay()
        print(f"Найдено товаров: {found_count}")

    except Exception as e:
        print(f"Ошибка парсинга: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает. Напиши секретный код.")


async def secret_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if message == SECRET_CODE:
        await update.message.reply_text(str(found_count))


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Нет BOT_TOKEN")

    if not FUNPAY_URL:
        raise RuntimeError("Нет FUNPAY_URL")

    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, secret_code_handler))

    app.job_queue.run_repeating(
        check_funpay,
        interval=60,
        first=5
    )

    app.run_polling()


if __name__ == "__main__":
    main()
