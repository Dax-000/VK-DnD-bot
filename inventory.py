import sqlite3
from utility import db_connect


def ini_inventory():
    with db_connect(True) as db:
        try:
            db.execute('''
                CREATE TABLE IF NOT EXISTS Players (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                items TEXT DEFAULT '',
                gold INTEGER DEFAULT 0 CHECK (typeof(gold) = "integer"),
                old_items TEXT DEFAULT '',
                old_gold INTEGER DEFAULT 0 CHECK (typeof(old_gold) = "integer"),
                updated BLOB DEFAULT FALSE
                );
            ''')
            db.execute('''CREATE TABLE IF NOT EXISTS Chats (
                    chat_id INTEGER primary key,
                    chat_name TEXT,
                    members TEXT,
                    creation_date TEXT
                )
            ''')
            db.execute('''CREATE TRIGGER IF NOT EXISTS new_chat AFTER INSERT
                ON Chats
                BEGIN
                UPDATE Chats SET creation_date = datetime('now') WHERE chat_id = NEW.chat_id;
                END;
            ''')
            db.execute('''CREATE TRIGGER IF NOT EXISTS upd AFTER UPDATE
                OF items, gold ON Players
                FOR EACH ROW
                BEGIN
                UPDATE Players SET updated = TRUE WHERE ROWID = NEW.ROWID;
                END;
            ''')
        except:
            print("ini_inventoty: не удалось инициировать базу данных")
        else:
            print("ini_inventoty: инициирована база данных")


def db_id_exist(_id):
    with db_connect() as db:
        db.cur.execute("SELECT chat_id FROM Chats WHERE chat_id = ?", (_id,))
        return db.fetchone() is not None


def db_new_inventory(_chat_id, _chat_name, _profiles):
    print('db_new_inventory: начало создания нового инвентаря')
    members = ''
    for member in _profiles:
        members += f"{member['first_name']} {member['last_name']}, "
    data_tuple = (_chat_id, _chat_name, members)

    with db_connect(True) as db:
        try:
            db.execute('''INSERT INTO Chats (chat_id, chat_name, members) VALUES (?, ?, ?);''', data_tuple)
            print('db_new_inventory: создана новая запись в таблице Chats')
            for player in _profiles:
                player_data = (_chat_id, player['id'], player['first_name'])
                db.execute('''INSERT INTO Players (chat_id, user_id, username) VALUES (?, ?, ?);''', player_data)
        except:
            print('db_new_inventory: ошибка, изменения отменены')
            return f'Не удалось создать инвентарь для беседы \"{_chat_name}\"'
        else:
            print('db_new_inventory: созданы новые записи в таблице Players')
            return f"Создан инвентарь для беседы \"{_chat_name}\""


def new_inventory(_chat_id, _chat_name, _profiles):
    if db_id_exist(_chat_id):
        return f'Для беседы \"{_chat_name}\" инвентарь уже создан'
    else:
        return db_new_inventory(_chat_id, _chat_name, _profiles)


def db_get_inventory(_user_id, _chat_id):
    connection = sqlite3.connect('players_inventory.db')
    cursor = connection.cursor()
    try:
        cursor.execute(f'''SELECT username, items, gold FROM Players WHERE user_id =? AND chat_id=?''',
                       (_user_id, _chat_id))
        selection = cursor.fetchone()
        connection.close()
        print(f'show_inventory: получено содержимое инвентаря user_id:{_user_id}, chat_id:{_chat_id}')
        return selection
    except:
        connection.close()
        print(f'show_inventory: ошибка доступа инвентаря user_id:{_user_id}, chat_id:{_chat_id}')
        return None


def text_get_inventory(_player_name, _player_items, _player_gold):
    start_str = f'{_player_name}, в твоём инвентаре:\n'
    inv_content = ''
    i = 0
    for item in _player_items.split(', '):
        if item:
            i += 1
            inv_content += f'{i}) {item}\n'
    if _player_gold:
        inv_content += f'{_player_gold} золота'
    if inv_content == '':
        inv_content = '*ничего*'
    return start_str + inv_content


def show_inventory(_user_id, _chat_id):
    selection = db_get_inventory(_user_id, _chat_id)
    if selection:
        player_name = selection[0]
        player_items = selection[1]
        player_gold = selection[2]
    else:
        print(f'show_inventory: инвентарь user_id:{_user_id}, chat_id:{_chat_id} не найден')
        return "Инвентарь не найден"
    print('show_inventory: получен текст состава инвентаря')
    return text_get_inventory(player_name, player_items, player_gold)


def text_item_difference(_new_items, _old_items, _gold, _old_gold):
    new_set = set(_new_items.split(", "))
    old_set = set(_old_items.split(", "))
    plus = new_set - old_set - {""}
    minus = old_set - new_set - {""}
    delta_gold = _gold - _old_gold
    item_gold = f"{abs(delta_gold)} золота"
    if delta_gold > 0:
        plus.add(item_gold)
    elif delta_gold < 0:
        minus.add(item_gold)
    ret_str = ""
    if plus:
        ret_str += " получено: "
        for item in plus:
            ret_str += f'{item} '

    if minus:
        ret_str += " потрачено: "
        for item in minus:
            ret_str += f'{item} '
    if not ret_str.replace(' ', ''):
        ret_str = ' ты умничка~'
    print('text_item_difference: получен текст ответа изменения инвентаря игрока')
    return ret_str


def inventory_difference(_fetch):
    ret_arr = []
    ch_id = -1
    j = -1
    for note in _fetch:
        _id = note[0]
        _name = note[1]
        _message = text_item_difference(note[2], note[3], note[4], note[5])
        if _id != ch_id:
            ret_arr.append([_id, f'{_name},{_message}'])
            ch_id = _id
            j += 1
        else:
            ret_arr[j][1] += f'\n{note[1]},{_message}'
    print('inventory_difference: получен текст ответа изменения инвентаря всех игроков')
    return ret_arr


def get_db_inventory_update():
    connection = sqlite3.connect('players_inventory.db')
    cursor = connection.cursor()
    cursor.execute(
        "SELECT chat_id, username, items, old_items, gold, old_gold FROM Players WHERE updated = TRUE ORDER BY chat_id")
    fetch = cursor.fetchall()
    connection.close()
    return fetch


def check_inventory():
    fetch = get_db_inventory_update()
    if not fetch:
        return []
    else:
        connection = sqlite3.connect('players_inventory.db')
        cursor = connection.cursor()
        cursor.execute('BEGIN')
        try:
            cursor.execute('''UPDATE Players SET updated = FALSE''', ())
            print('check_inventory: флаги обновления инвентаря сброшены')
            diff = inventory_difference(fetch)
            cursor.execute('''UPDATE Players SET old_items = items, old_gold = gold''', ())
            print("check_inventory: old значения обновлены")
            cursor.execute('COMMIT')
            connection.close()
            return diff
        except:
            print('check_inventory: инвентарь редактируется. Ожидание внесения изменений')
            cursor.execute('ROLLBACK')
            connection.close()
            return []
