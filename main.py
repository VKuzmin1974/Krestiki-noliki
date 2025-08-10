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
    if uid in db["users"]:
        await message.answer('Вы уже зарегистрированы')
    else:
        db["users"][uid] = {'state': 'ожидание'}
        save_json(db)
        await message.answer('Добро пожаловать')

@dp.message(Command('create'))
async def create(message: types.message):
    uid = str(message.from_user.id)
    if db["users"][uid]["state"] == 'ожидание':
        g_id = random.randint(1000, 9999)
        g_counter = 0
        while g_id in db["games"]:
            g_id = random.randint(1000, 9999)
            g_counter += 1
            if g_counter > 10:
                await message.answer('Не удалось создать игру. Попробуйте позже.')
                return
        g_id = str(g_id)
        db["games"][g_id] = {'move': 'крестики',
                             'player1': uid,
                             'player2': None,
                            'table': ['.', '.', '.', '.', '.', '.', '.', '.', '.']}
        db["users"][uid]["state"] = 'играет'
        db["users"][uid]["game"] = g_id
        db["users"][uid]["point"] = 'крестики'


        await message.answer(f"Вы создали игру, ее номер {g_id}. \n"
                            f"{print_table(db['games'][g_id]['table'])}")
        save_json(db)
    else:
        await message.answer('Не удалось создать игру. Попробуйте позже.')


@dp.message(Command('join'))
async def join(message: types.message):
    uid = str(message.from_user.id)
    if db["users"][uid]["state"] == 'ожидание':
        if message.text.count(' ') > 0:
            arg = message.text.split(' ')[1]
            if arg in db["games"]:
                db["users"][uid]["state"] = 'играет'
                db["users"][uid]["game"] = arg
                db["users"][uid]["point"] = 'нолики'
                db["games"][arg]["player2"] = uid
                save_json(db)
                if db["games"][arg]['move'] == "крестики":
                    await message.answer(f'Вы подключились к игре, но сейчас не Ваш ход')
                else:
                    await message.answer(print_table(db["games"][arg]["table"]))
            else:
                await message.answer('Нет такой игры')
        else:
            await message.answer('Введите /join номер игры (например, /join 1234)')
    else:
        await message.answer('Не удалось подключиться')


@dp.message(Command('stop'))
async def stop(message: types.message):
    uid = str(message.from_user.id)
    if db["users"][uid]["state"] == 'играет':
        g_id = db["users"][uid]["game"]
        uid = db["games"][g_id]["player1"]
        db["users"][uid]["state"] = 'ожидание'
        p2 = db["games"][g_id].get("player2")
        if p2:
            db["users"][p2]["state"] = 'ожидание'
            db["users"][p2]["game"] = None
        del db["games"][g_id]
        db["users"][uid]["game"] = None
        save_json(db)


def print_table(table):
    return (f'Сейчас Ваш ход, выберите клетку от 1 до 9\n'
            f'1 2 3\n'
            f'4 5 6\n'
            f'7 8 9\n\n'
            f'{table[0]} {table[1]} {table[2]}\n'
            f'{table[3]} {table[4]} {table[5]}\n'
            f'{table[6]} {table[7]} {table[8]}\n')


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


