from config import hotels_bot  # noqa: D100

from telebot import types

from utils import city_definition, empty_dictionary, search_data


@hotels_bot.message_handler(commands=['bestdeal'])
def command_bestdeal(message: types.Message) -> None:
    """
    Функция - обработчик команды пользователя '/bestdeal'.
    Подготавливает словари-хранилища информации поискового запроса для начала работы.
    Создаёт в словаре-хранилище отдельный словарь для каждого пользователя,
    куда сохраняются полученные от него данные дл поиска.
    Перенаправляет работу на обработчик 'city_definition' модуля 'utils'.

    :param message: сообщение пользователя
    :type message: telebot.types.Message
    """
    empty_dictionary(message.from_user.id)
    search_data[message.from_user.id].setdefault('search_command', 'Bestdeal')
    search_data[message.from_user.id].setdefault('search_pattern', 'PRICE')
    city_question = 'В каком городе хотите найти отель?'
    hotels_bot.send_message(message.from_user.id, city_question)
    hotels_bot.register_next_step_handler(message, city_definition)
