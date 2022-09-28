"""
Модуль с конфигурационными настройками и данными, которые требуются на разных этапах работы бота.


BOT_TOKEN - токен телеграм-бота, который хранится в среде окружения.
hotels_bot - объект TeleBot.
headers - словарь с ключом RapidAPI, а также host RapidAPI.
main_url - основной url сервиса с API, по которому происходят все запросы.
tg_api_url = url, требующийся для запросов через API Telegram.
ORIGINAL_COMMANDS - кортеж с парами "название команды" - "описание команды". Список возможностей бота.

search_data - словарь для сохранения данных, полученных от пользователя, по которым проводится поиск отелей.
search_result - словарь с результатами поиска, который проводил пользователь.
"""

import os

from dotenv import load_dotenv

import telebot


load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
hotels_bot = telebot.TeleBot(BOT_TOKEN)

headers = {
    "X-RapidAPI-Key": os.environ.get('X-RapidAPI-Key'),
    "X-RapidAPI-Host": 'hotels4.p.rapidapi.com'
}
main_url = 'https://hotels4.p.rapidapi.com'
tg_api_url = 'https://api.telegram.org/bot'

search_data = dict()
search_result = dict()

ORIGINAL_COMMANDS = (
    ('start', 'запуск бота HotelsEasy'),
    ('help', 'справка по возможностям бота'),
    ('lowprice', 'поиск самых дешёвых отелей в городе'),
    ('highprice', 'поиск самых дорогих и комфортных отелей в городе'),
    ('bestdeal', 'поиск отелей, наиболее подходящих по цене и расположению '
        'от центра'),
    ('history', 'вывод истории поиска отелей')
)
