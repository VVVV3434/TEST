import os
import re
import pandas as pd
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

TOKEN = os.getenv("BOT_TOKEN")
LIMIT = 50
FILE_NAME = "hotels_spb_test.xlsx"

SEARCH_URLS = [
    "https://yandex.ru/maps/2/saint-petersburg/search/отели/",
    "https://yandex.ru/maps/2/saint-petersburg/search/гостиницы/",
    "https://yandex.ru/maps/2/saint-petersburg/search/хостелы/",
    "https://yandex.ru/maps/2/saint-petersburg/search/гостевые%20дома/",
]

def clean(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

async def scrape_yandex_maps(limit=50):
    results = []
    seen_links = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = await browser.new_page(
            viewport={"width": 1366, "height": 768},
            locale="ru-RU"
        )

        for url in SEARCH_URLS:
            if len(results) >= limit:
                break

            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            for _ in range(15):
                await page.mouse.wheel(0, 2500)
                await page.wait_for_timeout(1000)

            links = await page.locator("a[href*='/org/']").evaluate_all(
                """els => [...new Set(els.map(a => a.href).filter(h => h.includes('/org/')))]"""
            )

            for link in links:
                if len(results) >= limit:
                    break

                if link in seen_links:
                    continue

                seen_links.add(link)

                try:
                    await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3500)

                    title = ""
                    if await page.locator("h1").count():
                        title = clean(await page.locator("h1").first.text_content())

                    phone = ""
                    if await page.locator("a[href^='tel:']").count():
                        phone = clean(await page.locator("a[href^='tel:']").first.text_content())

                    site = ""
                    site_links = await page.locator("a[href^='http']").evaluate_all(
                        """els => els.map(a => a.href).filter(h =>
                            !h.includes('yandex') &&
                            !h.includes('booking') &&
                            !h.includes('ostrovok') &&
                            !h.includes('travel.yandex') &&
                            !h.includes('2gis') &&
                            !h.includes('google')
                        )"""
                    )
                    if site_links:
                        site = site_links[0]

                    description_parts = []

                    texts = await page.locator("body").inner_text()
                    for word in ["отель", "гостиница", "хостел", "гостевой дом", "3 звезды", "4 звезды", "5 звёзд", "спа", "ресторан", "парковка", "завтрак"]:
                        if word.lower() in texts.lower():
                            description_parts.append(word)

                    description = ", ".join(dict.fromkeys(description_parts))

                    if title:
                        results.append({
                            "Название отеля": title,
                            "Официальный сайт": site,
                            "Краткое описание": description,
                            "Номер телефона": phone,
                            "Ссылка на карточку отеля в картах": link
                        })

                        print(f"Собрано {len(results)}: {title}")

                except Exception as e:
                    print("Ошибка карточки:", link, e)

        await browser.close()

    df = pd.DataFrame(results)
    df.to_excel(FILE_NAME, index=False)
    return FILE_NAME, len(results)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "6666":
        await update.message.reply_text("Начинаю сбор тестовой базы на 50 объектов. Это может занять несколько минут.")

        try:
            file_path, count = await scrape_yandex_maps(LIMIT)

            await update.message.reply_document(
                document=open(file_path, "rb"),
                filename=file_path,
                caption=f"Готово. Собрано объектов: {count}"
            )

        except Exception as e:
            await update.message.reply_text(f"Ошибка при сборе: {e}")
            print("MAIN ERROR:", e)

    else:
        await update.message.reply_text("Напиши код 6666, чтобы собрать тестовый Excel.")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не найден в Environment Variables")

    print("Bot started")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
