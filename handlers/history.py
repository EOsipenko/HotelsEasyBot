import json  # noqa: D100

from config import hotels_bot

from telebot import types

from utils import info_pairs_formation, output_each_hotel_info


@hotels_bot.message_handler(commands=['history'])
def command_history(message: types.Message) -> None:
    """
    Функция - обработчик команды пользователя '/history'.
    Из сохранённых в файле 'search_requests.json' данных по поисковым запросам пользователя выводит ему
    последние 5 запросов.
    Если пользователь ранее ещё не использовал поиск с помощью бота, ему выводится соответствующее сообщение.

    :param message: сообщение пользователя
    :type message: telebot.types.Message
    """
    hotels_bot.send_message(message.from_user.id, 'Ваша история поиска:')

    with open('search_requests.json', 'r', encoding='utf-8') as req_file:
        all_requests_data = json.load(req_file)
        user_id = str(message.from_user.id)
        if user_id not in all_requests_data:
            error_text = 'Вы ещё не пользовались поиском'
            hotels_bot.send_message(message.from_user.id, error_text)
        else:
            for search_date, search_result in all_requests_data[user_id].items():
                output_text = []
                output_text.append('Дата поиска: {date}\n'.format(date=search_date))
                main_text = info_pairs_formation(search_result, 'Отели')
                output_text.extend(main_text)
                hotels_bot.send_message(message.from_user.id, '\n'.join(output_text))

                output_each_hotel_info(message, search_result['Отели'])
