import aiogram
import asyncio
from aiogram import Bot, Dispatcher, F, types
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
        db["users"][uid] = {'state': 'ожидание', 'wins': 0, 'losses': 0, 'ties': 0}
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
        await message.answer("игра остановлена")


@dp.message(F.text)
async def game(message: types.message):
    uid = str(message.from_user.id)
    if db["users"][uid]["state"] == 'завершение':
        g_id = db["users"][uid]["game"]
        p2 = db["games"][g_id]["player2"]
        p1 = db["games"][g_id]["player1"]
        if message.text.lower() == 'да':
            db["users"][p1]["state"] = 'играет'
            db["users"][p2]["state"] = 'играет'
            save_json(db)
            await bot.send_message(p2, print_table(db["games"][g_id]["table"]))
            await bot.send_message(p1, print_table(db["games"][g_id]["table"]))
            return
        db["users"][p1]["state"] = 'ожидание'
        db["users"][p2]["state"] = 'ожидание'
        db["users"][p2]["game"] = None
        db["users"][p1]["game"] = None
        del db["games"][g_id]
        save_json(db)
    if db["users"][uid]["state"] != 'играет':
        return
    if not message.text.isdigit():
        await message.answer('Введите число от 1 до 9.')
        return
    move = int(message.text)
    if not 1 <= move <= 9:
        await message.answer('Введите число от 1 до 9.')
        return
    g_id = db["users"][uid]["game"]
    if db["games"][g_id]["table"][move-1] != ".":
        await message.answer('Эта клетка уже занята')
        return
    if db["games"][g_id]['move'] != db["users"][uid]["point"]:
        await message.answer('Сейчас не Ваш ход')
        return
    if db["users"][uid]["point"] == 'крестики':
        db["games"][g_id]["table"][move - 1] = "X"
        db["games"][g_id]["move"] = "нолики"
        p2 = db["games"][g_id]["player2"]
        await bot.send_message(p2, print_table(db["games"][g_id]["table"]))
    else:
        db["games"][g_id]["table"][move - 1] = "0"
        db["games"][g_id]["move"] = "крестики"
        p1 = db["games"][g_id]["player1"]
        await bot.send_message(p1, print_table(db["games"][g_id]["table"]))
    state = check_table(db["games"][g_id]["table"])
    save_json(db)
    if not state:
        await message.answer('Ход сделан')
        return
    p2 = db["games"][g_id]["player2"]
    p1 = db["games"][g_id]["player1"]
    if state == 'крестики': # крестики выиграли
        db['users'][p1]['wins'] += 1
        db['users'][p2]['losses'] += 1
        await bot.send_message(p1, f'Вы победили. {get_stats(p1)}')
        await bot.send_message(p2, f'Вы проиграли. {get_stats(p2)}')
    if state == 'нолики': # нолики выиграли
        db['users'][p2]['wins'] += 1
        db['users'][p1]['losses'] += 1
        await bot.send_message(p2, f'Вы победили. {get_stats(p2)}')
        await bot.send_message(p1, f'Вы проиграли. {get_stats(p1)}')
    if state == 'ничья': # ничья
        db['users'][p2]['ties'] += 1
        db['users'][p1]['ties'] += 1
        await bot.send_message(p2, f'Ничья. {get_stats(p2)}')
        await bot.send_message(p1, f'Ничья. {get_stats(p1)}')
    db["users"][p1]["state"] = 'завершение'
    db["users"][p2]["state"] = 'завершение'
    db["games"][g_id]["table"] = ['.' for _ in range(9)]
    db["games"][g_id]["move"] = 'крестики'
    db["games"][g_id]["player1"] = p2
    db["games"][g_id]["player2"] = p1
    if db["users"][p1]["point"] == 'крестики':
        db["users"][p1]["point"] = 'нолики'
    else:
        db["users"][p1]["point"] = 'крестики'
    if db["users"][p2]["point"] == 'крестики':
        db["users"][p2]["point"] = 'нолики'
    else:
        db["users"][p2]["point"] = 'крестики'
    await bot.send_message(p2, f'Игра завершилась, если хотите реванш - "да"')
    await bot.send_message(p1, f'Игра завершилась, если хотите реванш - "да"')

    save_json(db)


def print_table(table):
    return (f'Сейчас Ваш ход, выберите клетку от 1 до 9\n'
            f'1 2 3\n'
            f'4 5 6\n'
            f'7 8 9\n\n'
            f'{table[0]} {table[1]} {table[2]}\n'
            f'{table[3]} {table[4]} {table[5]}\n'
            f'{table[6]} {table[7]} {table[8]}\n')


def check_table(table):
    m = {'X': 'крестики', '0': 'нолики'}
    if table[0] == table[1] == table[2] != '.':
        return m[table[0]]
    elif table[3] == table[4] == table[5] != '.':
        return m[table[3]]
    elif table[6] == table[7] == table[8] != '.':
        return m[table[7]]
    elif table[0] == table[4] == table[8] != '.':
        return m[table[4]]
    elif table[6] == table[4] == table[2] != '.':
        return m[table[6]]
    elif table[0] == table[3] == table[6] != '.':
        return m[table[0]]
    elif table[1] == table[4] == table[7] != '.':
        return m[table[1]]
    elif table[2] == table[5] == table[8] != '.':
        return m[table[8]]
    else:
        if '.' in table:
            return
        else:
            return 'ничья'


def get_stats(uid):
    return (
            f'Ваша статистика:\n'
            f'{db["users"][uid]["wins"]} побед\n'
            f'{db["users"][uid]["losses"]} поражений\n'
            f'{db["users"][uid]["ties"]} ничьих\n'
            )


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


