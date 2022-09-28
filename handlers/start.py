from config import hotels_bot  # noqa: D100

from telebot import types


@hotels_bot.message_handler(commands=['start'])
@hotels_bot.message_handler(regexp=r'[Пп]ривет')
def starting(message: types.Message):
    """
    Функция-приветствие, обработчик команды пользователя '/start' и 'Привет/привет'.
    Предлагает пользователю дать команду боту.

    :param message: сообщение пользователя
    :type message: telebot.types.Message
    """
    greeting = ('Привет! Я - бот турагентства Too Easy Travel.\n'
                'Скажите, что именно вас интересует, и я подберу лучшие варианты.\n'
                'Можете выбрать команду /help, и появится список моих возможностей.')
    hotels_bot.send_message(message.from_user.id, greeting)
