import aiogram
import asyncio
from aiogram import Bot, Dispatcher, types
import random
from os import getenv
from dotenv import load_dotenv
from aiogram.filters.command import Command
from fs import get_json, save_json


load_dotenv()
bot = Bot(getenv('TOKEN'))
dp = Dispatcher()
db = get_json()

@dp.message(Command('start'))
async def start(message: types.message):
    uid = str(message.from_user.id)
    if uid in db:
        await message.answer('Вы уже зарегистрированы')
    else:
        db[uid] = {'state': 'ожидание'}
        save_json(db)
        await message.answer('Добро пожаловать')





async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


