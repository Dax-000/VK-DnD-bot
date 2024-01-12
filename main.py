from random import choice
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from dotenv import dotenv_values

from utility import check_command_word, check_self_invite, is_for_me
from functionality import roll_dices, send_ankle_joke
from inventory import show_inventory, ini_inventory, new_inventory, check_inventory


COMMANDS = {
    # с обращением
    'hello': ['привет', 'здарова', 'здаров', 'салам алейкум', 'приветствую'],
    # 'exit': ['выйди', 'купи хлеб'],

    # без обращения
    'help': ['help', 'хелп'],
    'joke': ['анекдот', 'анек', 's g a', 'sga'],
    'show_inventory': ['инвентарь'],
    'roll': ['бросаю', 'бросаем', 'бросил', 'кидаю', 'кидаем', 'кинул'],
    'new_inventory': ['start', 'старт'],
}


ANSWERS = {
    'invite_me': 'Привет! Я буду помогать вести днд ролку. '
                 'Чтобы я могла видеть сообщения админ должен дать мне доступ ко всей переписке. '
                 'Список команд: help',
    'help': 'help, хелп: список команд\n'
            'start, старт: начать игру\n'
            'инвентарь: показать инвентарь\n'
            'анекдот, анек, sga: скинуть uncle joke\n'
            'бросаю, бросил, кидаю, кинул + d20 или 2д6: бросить кости',
    'hello': ['Привет', 'Здравствуйте', 'Рада тебя видеть', 'Здарова!'],
    'permission_error': 'Для выполнения команды необходимы права администратора'
}


def send_message(_id, text):
    try:
        vk_session.method('messages.send', {'chat_id': _id, 'message': text, 'random_id': 0})
    except:
        print(f'send_message: ошибка при отправке сообщения в чат {_id}')


def get_chat(_chat_id):
    request = vk_session.method('messages.getConversationsById', {'peer_ids': 2000000000 + _chat_id, 'extended': 1})
    if request['count']:
        return request
    else:
        raise PermissionError


def personal_request(_chat_id, _msg, _user_id):
    if check_command_word('hello', _msg, COMMANDS):
        send_message(_chat_id, choice(ANSWERS['hello']))
    # elif check_command_word('exit', _msg):
    #     vk_session.method('messages.removeChatUser', {'chat_id': _id, 'user_id': bot_id, 'member_id': -bot_id})


def general_request(_chat_id, _msg, _user_id):
    if check_command_word('roll', _msg, COMMANDS):
        send_message(_chat_id, roll_dices(_msg))
    elif check_command_word('help', _msg, COMMANDS):
        send_message(_chat_id, ANSWERS['help'])
    elif check_command_word('show_inventory', _msg, COMMANDS):
        send_message(_chat_id, show_inventory(_user_id, _chat_id))
    elif check_command_word('joke', _msg, COMMANDS):
        send_message(_chat_id, send_ankle_joke())
    elif check_command_word('new_inventory', _msg, COMMANDS):
        try:
            request = get_chat(_chat_id)
            title = request['items'][0]['chat_settings']['title']
            profiles = request['profiles']
            send_message(_chat_id, new_inventory(_chat_id, title, profiles))
        except PermissionError:
            send_message(_chat_id, ANSWERS['permission_error'])


if __name__ == "__main__":
    config = dotenv_values()
    token = config['token']
    bot_id = config['bot_id']
    bot_name = config['bot_name']
    # Подключаем токен и longpoll
    vk_session = vk_api.VkApi(token=token)
    longpoll = VkBotLongPoll(vk_session, bot_id)
    vk_session.get_api()
    ini_inventory()

    while True:
        for chat in check_inventory():
            send_message(chat[0], chat[1])
        for event in longpoll.check():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_chat:
                    msg = event.message.text.lower()
                    chat_id = event.chat_id
                    user_id = event.message['from_id']
                    if check_self_invite(event.message, bot_id):        # Приглашение в беседу бота
                        send_message(chat_id, ANSWERS['invite_me'])
                    elif is_for_me(msg, bot_name):                        # Сообщение содержит обращение к боту
                        personal_request(chat_id, msg, user_id)
                    else:
                        general_request(chat_id, msg, user_id)
