import requests
from re import search, split
from bs4 import BeautifulSoup
from random import randint


def roll_dices(_dices):
    _result = 'Выпало:'
    _sum = 0
    _dices_found = search(r'\b\d{0,3}[dд]\d{1,3}\b', _dices)
    if _dices_found:
        _dc = split(r'[dд]', _dices_found[0])
        value = int(_dc.pop(-1))
        quantity = 1
        if _dc[0] != '':
            quantity = int(_dc[0])
        if quantity == 0 or value == 0:
            return 'Выпало очко'
        for i in range(quantity):
            _dice = randint(1, value)
            _result += f' {_dice}'
            _sum += _dice

        if quantity > 2:
            _result += f'\nСумма: {_sum}'
        return _result
    else:
        return 'Я не поняла что ты кидаешь'


def send_ankle_joke():
    try:
        response = requests.get('https://randstuff.ru/joke/')
    except requests.ConnectionError:
        return 'Сейчас невозможно сгенерировать анекдот'
    else:
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="html.parser")
            anek = soup.find(id='joke').find('td').contents[0]
            return anek
        else:
            return 'Сейчас невозможно сгенерировать анекдот'
