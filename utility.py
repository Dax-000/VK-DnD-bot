from re import search
from contextlib import contextmanager
import sqlite3


@contextmanager
def db_connect(rollback=False):
    connection = sqlite3.connect('players_inventory.db')
    cur = connection.cursor()
    successful = True
    try:
        yield cur
    except:
        if rollback:
            connection.rollback()
        successful = False
    finally:
        if rollback and successful:
            connection.commit()
        connection.close()


def is_for_me(_message, _my_name):
    return bool(search(fr'\b{_my_name}\b', _message))


def check_self_invite(_message, _my_id):
    if _message.action:
        if 'chat_invite_user' in str(_message.action) and str(_my_id) in str(_message.action):
            return True
        print(_message.action)
    return False


def check_command_word(_word, _str, _comands_dict):
    if _word not in _comands_dict:
        print(f'Команды {_word} нет в словаре')
        return False
    else:
        for word in _comands_dict[_word]:
            if search(fr'\b{word}\b', _str):
                return True
        return False
