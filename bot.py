import os
import re
import pandas as pd
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)
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
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox"
            ]
        )

        page = await browser.new_page(
            viewport={"width": 1366, "height": 768},
            locale="ru-RU"
        )

        for url in SEARCH_URLS:

            if len(results) >= limit:
                break

            print(f"Открываю {url}")

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            await page.wait_for_timeout(5000)

            # Скроллим выдачу
            for _ in range(15):
                await page.mouse.wheel(0, 3000)
                await page.wait_for_timeout(1200)

            # Собираем ссылки карточек
            links = await page.locator(
                "a[href*='/org/']"
            ).evaluate_all(
                """
                els => [...new Set(
                    els
                    .map(a => a.href)
                    .filter(h => h.includes('/org/'))
                )]
                """
            )

            print(f"Найдено ссылок: {len(links)}")

            for link in links:

                if len(results) >= limit:
                    break

                if link in seen_links:
                    continue

                seen_links.add(link)

                try:
                    await page.goto(
                        link,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )

                    await page.wait_for_timeout(3000)

                    # Название
                    title = ""

                    if await page.locator("h1").count():
                        title = clean(
                            await page.locator("h1").first.text_content()
                        )

                    # Телефон
                    phone = ""

                    if await page.locator("a[href^='tel:']").count():
                        phone = clean(
                            await page.locator(
                                "a[href^='tel:']"
                            ).first.text_content()
                        )

                    # Сайт
                    site = ""

                    links_found = await page.locator(
                        "a[href^='http']"
                    ).evaluate_all(
                        """
                        els => els
                        .map(a => a.href)
                        .filter(h =>
                            !h.includes('yandex') &&
                            !h.includes('booking') &&
                            !h.includes('ostrovok') &&
                            !h.includes('travel.yandex') &&
                            !h.includes('google') &&
                            !h.includes('2gis')
                        )
                        """
                    )

                    if links_found:
                        site = links_found[0]

                    # Описание
                    description_parts = []

                    body_text = await page.locator(
                        "body"
                    ).inner_text()

                    keywords = [
                        "отель",
                        "гостиница",
                        "хостел",
                        "гостевой дом",
                        "3 звезды",
                        "4 звезды",
                        "5 звезд",
                        "SPA",
                        "спа",
                        "ресторан",
                        "завтрак",
                        "парковка"
                    ]

                    for word in keywords:
                        if word.lower() in body_text.lower():
                            description_parts.append(word)

                    description = ", ".join(
                        dict.fromkeys(description_parts)
                    )

                    if title:

                        results.append({
                            "Название отеля": title,
                            "Официальный сайт": site,
                            "Краткое описание": description,
                            "Номер телефона": phone,
                            "Ссылка на карточку в картах": link
                        })

                        print(
                            f"Собрано {len(results)}: {title}"
                        )

                except Exception as e:
                    print("Ошибка карточки:", e)

        await browser.close()

    df = pd.DataFrame(results)
    df.to_excel(FILE_NAME, index=False)

    return FILE_NAME, len(results)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip()

    if text == "6666":

        await update.message.reply_text(
            "Начинаю сбор тестовой базы (50 объектов). Это может занять несколько минут..."
        )

        try:
            file_path, count = await scrape_yandex_maps(LIMIT)

            await update.message.reply_document(
                document=open(file_path, "rb"),
                filename=file_path,
                caption=f"Готово. Собрано объектов: {count}"
            )

        except Exception as e:
            print("MAIN ERROR:", e)

            await update.message.reply_text(
                f"Ошибка при сборе:\n{e}"
            )

    else:
        await update.message.reply_text(
            "Напиши 6666"
        )


async def post_init(app):
    await app.bot.delete_webhook(
        drop_pending_updates=True
    )


def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не найден"
        )

    print("Bot started")

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
