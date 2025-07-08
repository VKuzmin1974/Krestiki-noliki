import aiogram
import asyncio
from aiogram import Bot, Dispatcher, types
import random
from os import getenv
from dotenv import load_dotenv


load_dotenv()
bot = Bot(getenv('TOKEN'))
dp = Dispatcher()

async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


