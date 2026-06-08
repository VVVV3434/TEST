import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = os.getenv("8867608436:AAGRMJj26VODPBnE0Vte4dAXQ6zVArc73iE")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Проверь Environment Variables в Render.")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("✅ Это новый чистый бот. Работает только наш код.")


@dp.message()
async def any_message(message: types.Message):
    await message.answer("Я получил сообщение. Всё ок.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
 
