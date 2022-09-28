"""
Основной скрипт проекта, с которого производится запуск работы бота:
устанавливаются команды, по которым происходит работа с ботом,
и запускается бесконечное 'прослушивание' сообщений от пользователя.
"""
from config import hotels_bot

import handlers  # noqa: F401

import keyboards  # noqa: F401

from set_bot_commands import set_default_commands


if __name__ == '__main__':
    set_default_commands(hotels_bot)
    hotels_bot.infinity_polling()
