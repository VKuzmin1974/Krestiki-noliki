from json import dumps, loads


def save_json(db):
    with open('db.json', 'w', encoding='UTF-8') as file:
        file.write(dumps(db, indent=4))


def get_json():
    with open('db.json', 'r', encoding='UTF-8') as file:
        return loads(file.read())

