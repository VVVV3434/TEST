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

found_items = []

web_app = Flask(__name__)


@web_app.get("/")
def home():
    return "Bot is running"


def run_web():
    port = int(os.getenv("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


def convert_to_rubles(text):
    text = text.lower().replace(",", ".")

    price_match = re.search(r"(\d+(?:\.\d+)?)\s*(₽|руб|rub)", text)

    if price_match:
        return float(price_match.group(1))

    dollar_match = re.search(r"\$(\d+(?:\.\d+)?)", text)

    if dollar_match:
        return float(dollar_match.group(1)) * 90

    euro_match = re.search(r"€(\d+(?:\.\d+)?)", text)

    if euro_match:
        return float(euro_match.group(1)) * 100

    return None


def parse_funpay():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(FUNPAY_URL, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    items = []

    offers = soup.find_all("a", href=True)

    for offer in offers:
        text = offer.get_text(" ", strip=True)
        href = offer["href"]

        if not text:
            continue

        rub_price = convert_to_rubles(text)

        if rub_price is None:
            continue

        if MIN_PRICE <= rub_price <= MAX_PRICE:
            url = href if href.startswith("http") else "https://funpay.com" + href

            items.append({
                "title": text[:120],
                "price": int(rub_price),
                "url": url
            })

    return items


async def check_funpay(context: ContextTypes.DEFAULT_TYPE):
    global found_items

    try:
        found_items = parse_funpay()
        print(f"Найдено товаров: {len(found_items)}")

    except Exception as e:
        print(f"Ошибка парсинга: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает. Напиши секретный код.")


async def secret_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if message != SECRET_CODE:
        return

    if not found_items:
        await update.message.reply_text("0")
        return

    await update.message.reply_text(str(len(found_items)))

    text = ""

    for i, item in enumerate(found_items, start=1):
        line = f"{i}. {item['price']} ₽ — {item['url']}\n"

        if len(text) + len(line) > 3500:
            await update.message.reply_text(text)
            text = ""

        text += line

    if text:
        await update.message.reply_text(text)


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
