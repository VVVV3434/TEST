import os
import re
import asyncio
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
        page = await browser.new_page()

        for url in SEARCH_URLS:
            if len(results) >= limit:
                break

            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # скроллим список
            for _ in range(12):
                await page.mouse.wheel(0, 2500)
                await page.wait_for_timeout(1200)

            cards = await page.locator("a[href*='/org/']").all()

            links = []
            for card in cards:
                href = await card.get_attribute("href")
                if href and "/org/" in href:
                    if href.startswith("/"):
                        href = "https://yandex.ru" + href
                    if href not in seen_links:
                        seen_links.add(href)
                        links.append(href)

            for link in links:
                if len(results) >= limit:
                    break

                try:
                    await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3000)

                    title = clean(await page.locator("h1").first.text_content())

                    phone = ""
                    phone_el = page.locator("a[href^='tel:']").first
                    if await phone_el.count():
                        phone = clean(await phone_el.text_content())

                    site = ""
                    site_el = page.locator("a[href^='http']").filter(has_text=re.compile(r"\.")).first
                    if await site_el.count():
                        site = await site_el.get_attribute("href") or ""

                    description_parts = []

                    cats = await page.locator(".business-card-title-view__categories a, .business-categories-view__category").all()
                    for c in cats[:5]:
                        txt = clean(await c.text_content())
                        if txt:
                            description_parts.append(txt)

                    features = await page.locator(".business-features-view__valued-value, .business-features-view__bool-text").all()
                    for f in features[:10]:
                        txt = clean(await f.text_content())
                        if txt:
                            description_parts.append(txt)

                    description = ", ".join(dict.fromkeys(description_parts))

                    results.append({
                        "Название отеля": title,
                        "Официальный сайт": site,
                        "Краткое описание": description,
                        "Номер телефона": phone,
                        "Ссылка на карточку в картах": link
                    })

                except Exception as e:
                    print("Ошибка карточки:", link, e)

        await browser.close()

    df = pd.DataFrame(results)
    df.to_excel(FILE_NAME, index=False)
    return FILE_NAME, len(results)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "6666":
        await update.message.reply_text("Собираю тестовую базу на 50 объектов...")

        file_path, count = await scrape_yandex_maps(LIMIT)

        await update.message.reply_document(
            document=open(file_path, "rb"),
            filename=file_path,
            caption=f"Готово. Собрано объектов: {count}"
        )
    else:
        await update.message.reply_text("Напиши код 6666")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
