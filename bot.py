import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# Берём токен из Render Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверка что токен найден
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не найден. Проверь Environment Variables в Render."
    )

# Создаём бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Команда /start
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "✅ Это новый чистый бот. Работает только наш код."
    )


# Ответ на любое сообщение
@dp.message()
async def any_message(message: types.Message):
    await message.answer(
        f"Вы написали: {message.text}"
    )


# Запуск бота
async def main():
    # Удаляем старые webhook'и и конфликты
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
