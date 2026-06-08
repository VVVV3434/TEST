import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Привет! Бот работает 🚀")


@dp.message()
async def echo(message: types.Message):
    text = message.text.lower()

    if "привет" in text:
        await message.answer("И тебе привет!")

    else:
        await message.answer(f"Ты написал: {message.text}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
