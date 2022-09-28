"""
Модуль, который занимается обработкой данных, получаемых от пользователя в чате с ботом, и выводит
результаты поиска отелей.
"""

import json
import re
from datetime import datetime
from operator import itemgetter
from typing import Any, Dict, List, Union

from config import BOT_TOKEN, headers, hotels_bot, main_url, search_data, search_result, tg_api_url

from keyboards.size_9_keyboard import get_keyboard

import requests

from telebot import types


def empty_dictionary(user_id: int) -> None:
    """
    Функция очищает словари search_data и search_result для конкретного пользователя (по его ID).
    Это требуется для того, чтобы новые данные при новом поисковом запросе не накладывались
    на старые и не было путаницы между данных разных пользователей.
    """
    try:
        search_data[user_id].clear()
        search_result[user_id].clear()
    except KeyError:
        search_data.setdefault(user_id, dict())
        search_result.setdefault(user_id, dict())


def info_pairs_formation(dictionary: Dict[str, Union[str, float, list]], *exceptions: str) -> List[str]:
    """
    Функция составляет список строк-пар 'заголовок: значение' из полученного словаря.
    Если есть слова-исключения, то функция пропускает эти ключи в словаре.

    :param dictionary: словарь, из элементов которого составляются пары
    :type dictionary: Dict[str, str | float | list]

    :param exceptions: ключи словаря, которые следует пропускать
    :type exceptions: str

    :return: info - список строковых пар
    :rtype: List[str]
    """
    info = ['{header}: {content}'.format(header=header, content=content)
            for header, content in dictionary.items() if header not in exceptions]
    return info


def output_each_hotel_info(message: types.Message, hotels_list: List[dict]) -> None:
    """
    Функция обрабатывает получаемый список словарей и в качестве сообщения пользователю выводит
    информацию по каждому отелю, в том числе фотографии.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :param hotels_list: список словарей (один словарь - один отель)
    :type hotels_list: List[dict]
    """
    for hotel in hotels_list:
        hotel_info = info_pairs_formation(hotel, 'Фото', 'ID')
        hotels_bot.send_message(message.from_user.id, '\n'.join(hotel_info))
        if hotel['Фото']:
            for image_url in hotel['Фото']:
                send_photo(message.from_user.id, image_url)


def get_request_data(message: types.Message,
                     url_part: str,
                     querystring: Dict[str, str],
                     error_text: str) -> Dict[str, Any]:
    """
    Функция отправляет запрос через API на получение данных.
    В случае, если статус ответа не "200", вызывается и обрабатывается исключение.

    Функция возвращает десериализованный json-объект (словарь).

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :param url_part: часть url, отвечающая за конкретный запрос
    :type url_part: str

    :param querystring: параметры запроса
    :type querystring: Dict[str, str]

    :param error_text: текст, который будет выведен пользователю в случае возникновения
        исключения (если код ответа не равен 200)
    :type error_text: str

    :return: json.loads(response.text) - десериализованный json-объект (словарь)
    :rtype: Dict[str, Any]

    :raises ValueError: если код ответа не равен 200, вызывается исключение;
        обработка: пользователю в чате присылается сообщение об ошибке

    :raises json.decoder.JSONDecodeError: если формат ответа от сервера некорректен;
        обработка: пользователю в чате присылается сообщение об ошибке с просьбой начать поиск снова
    """
    url = main_url + url_part
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            raise ValueError
    except ValueError:
        hotels_bot.send_message(message.from_user.id, error_text)
    else:
        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            error_text = ('Некорректный ответ от сервера.\n'
                          'Пожалуйста, подождите и попробуйте начать поиск снова')
            hotels_bot.send_message(message.from_user.id, error_text)


def days_calculation(check_in: datetime, check_out: datetime) -> int:
    """
    Вычисление количества дней между датами.
    Если даты совпадают, то возвращается 1, так как предполагается, что отелем
    будет взиматься оплата минимум за 1 сутки.

    :param check_in: дата заезда в отель
    :type check_in: datetime.datetime

    :param check_out: дата выезда из отеля
    :type check_out: datetime.datetime

    :return: delta - количество дней между датами
    :rtype: int
    """
    difference = str(check_out - check_in)
    delta = int(re.match(r'\d+', difference).group())
    if delta == 0:
        return 1
    return delta


def hotel_info_filling(message: types.Message, i_hotel: Dict[str, Any]) -> None:
    """
    Функция создаёт словарь для отеля и заполняет его нужными данными.
    В качестве источника данных для функции выступает полученный от API словарь по конкретному отелю.
    В итоге созданный словарь добавляется в список отелей словаря с результатами поиска.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :param i_hotel: словарь, полученный от API, с данными отеля, которые нужно обработать
    :type i_hotel: Dict[str, Any]
    """
    hotel = dict()
    hotel['Название'] = i_hotel['name']
    hotel['Цена, $'] = i_hotel['ratePlan']['price']['exactCurrent']
    hotel['Цена за все дни, $'] = round(hotel['Цена, $']
                                        * search_data[message.from_user.id]['dates']['days_of_stay'], 2)
    hotel['От центра'] = i_hotel['landmarks'][0]['distance']
    hotel['ID'] = i_hotel['id']
    address_adding(message, hotel)
    hotel['Ссылка на отель'] = 'https://www.hotels.com/ho{id}/'.format(id=i_hotel['id'])

    hotel['Фото'] = []
    if search_data[message.from_user.id]['photo_number'] != 'none':
        photo_adding(message, hotel)

    try:
        search_result[message.from_user.id]['Отели'].append(hotel)
    except KeyError('Отели'):
        search_result[message.from_user.id]['Отели'] = []
        search_result[message.from_user.id]['Отели'].append(hotel)


def photo_adding(message: types.Message, hotel: Dict[str, Union[str, list]]) -> None:
    """
    Функция добавляет ссылки на фото отеля в словарь конкретного отеля.
    В начале процесса отправляется запрос к API Hotels.com.
    В случае, если запрос к API будет неуспешным, пользователю в чат будет выведено соответствующее сообщение и
    фото добавлены не будут.

    Если пользователь ранее указывал требуемое количество фотографий n не равное 1, то
    добавляется n-1 фото номеров отеля и одно фото самого отеля. Если n=1, то добавляется
    только фото произвольного номера отеля.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :param hotel: формируемый словарь конкретного отеля
    :type hotel: Dict[str, str | list]

    :raises ValueError: если код ответа не равен 200, вызывается исключение;
        обработка: пользователю в чате присылается сообщение об ошибке
    """
    photo_url_part = '/properties/get-hotel-photos/'
    querystring = {"id": hotel['ID']}
    photo_error_text = ('Что-то не так с ответом сервера по фото отеля {name}...'.format(
                        name=hotel['Название']),
                        'Фото выведены не будут.')
    photo_error_text = '\n'.join(photo_error_text)
    photo_data = get_request_data(message, photo_url_part, querystring, photo_error_text)
    if all((photo_data, photo_data['roomImages'], photo_data['hotelImages'])):
        photo_num = 0
        for r_count, room in enumerate(photo_data['roomImages'], 1):
            image_url = room['images'][0]['baseUrl'].format(size='y')
            hotel['Фото'].append(image_url)
            if (r_count == search_data[message.from_user.id]['photo_number'] - 1) or (
                    search_data[message.from_user.id]['photo_number'] == 1):
                photo_num = r_count
                break
        if search_data[message.from_user.id]['photo_number'] != 1:
            for h_count, hotels_image in enumerate(photo_data['hotelImages'], 1):
                image_url = hotels_image['baseUrl'].format(size='y')
                hotel['Фото'].append(image_url)
                if h_count == search_data[message.from_user.id]['photo_number'] - photo_num:
                    break
    else:
        hotels_bot.send_message(message.from_user.id, photo_error_text)


def address_adding(message: types.Message, hotel: Dict[str, Union[str, list]]) -> None:
    """
    Функция добавляет адрес в словарь конкретного отеля.
    В начале процесса отправляется запрос к API Hotels.com.
    В случае, если запрос к API будет неуспешным, пользователю в чат будет выведено соответствующее сообщение и
    элемент 'Адрес' в формируемый словарь добавлен не будет.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :param hotel: формируемый словарь конкретного отеля
    :type hotel: Dict[str, str | list]

    :raises ValueError: если код ответа не равен 200, вызывается исключение;
        обработка: пользователю в чате присылается сообщение об ошибке
    """
    details_url_part = '/properties/get-details/'
    querystring = {"id": hotel['ID'],
                   "checkIn": search_data[message.from_user.id]['dates']['check_in'],
                   "checkOut": search_data[message.from_user.id]['dates']['check_out'],
                   "adults1": "1",
                   "currency": "USD",
                   "locale": "ru_RU"}
    details_error_text = ('Что-то не так с ответом сервера по адресу отеля {name}...'.format(
                          name=hotel['Название']),
                          'Точный адрес выведен не будет.')
    details_error_text = '\n'.join(details_error_text)
    details_data = get_request_data(message, details_url_part, querystring, details_error_text)
    if details_data:
        hotel['Адрес'] = details_data['data']['body']['propertyDescription']['address']['fullAddress']


def send_photo(user_id: str, img_url: str) -> None:
    """
    Функция осуществляет запрос к Telegram API для получения фото в чате по ID пользователя.

    :param user_id: ID пользователя
    :type user_id: str

    :param img_url: web-ссылка на фотографию
    :type img_url: str
    """
    requests.get('{tg_api_url}{token}/sendPhoto?chat_id={user_id}&photo={img_url}'.format(
                 tg_api_url=tg_api_url,
                 token=BOT_TOKEN,
                 user_id=user_id,
                 img_url=img_url))


def search_result_output(message: types.Message) -> None:
    """
    Функция отвечает за вывод пользователю сообщения в чат с результатами поиска отелей.
    Если по заданным ранее критериям найти ничего не удалось, пользователю будет отправлено
    соответствующее сообщение.
    В итоге результаты поиска сохраняются в search_requests.json по id пользователя.

    :param message: сообщение пользователя
    :type message: telebot.types.Message
    """
    hotels_bot.send_message(message.from_user.id, 'Результаты поиска')
    initial_data = '\n'.join(('Даты: {dates}'.format(dates=search_data[message.from_user.id]['dates']['dates_of_stay']),
                              'Город: {city}'.format(city=search_result[message.from_user.id]['Город'])))
    hotels_bot.send_message(message.from_user.id, initial_data)

    selected_hotels = search_result[message.from_user.id]['Отели']
    if not selected_hotels:
        hotels_error_text = 'По выбранным критериям ничего найти не удалось('
        hotels_bot.send_message(message.from_user.id, hotels_error_text)

    output_each_hotel_info(message, selected_hotels)
    user_id = str(message.from_user.id)
    saving_search_request(user_id)


def search_for_matches(message: types.Message) -> None:
    """
    Функция, выполняющая поиск отелей по заданным ранее критериям.
    В начале процесса отправляется запрос к API Hotels.com.
    В случае, если запрос к API будет неуспешным, пользователю в чат будет выведено соответствующее сообщение и
    процесс работы поисковой функции будет прекращён.
    В итоге результаты поиска сохраняются в search_requests.json по id пользователя.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :raises ValueError: если код ответа не равен 200, вызывается исключение;
        обработка: пользователю в чате присылается сообщение об ошибке
    """
    properties_url_part = '/properties/list/'
    querystring = {
        "destinationId": search_data[message.from_user.id]['destination_id'],
        "pageNumber": "1",
        "pageSize": "25",
        "checkIn": search_data[message.from_user.id]['dates']['check_in'],
        "checkOut": search_data[message.from_user.id]['dates']['check_out'],
        "adults1": "1",
        "sortOrder": search_data[message.from_user.id]['search_pattern'],
        "locale": "ru_RU",
        "currency": "USD"}
    matches_error_text = ('Что-то не так с ответом сервера по деталям отеля...')

    properties_data = get_request_data(message, properties_url_part, querystring, matches_error_text)
    if properties_data:
        search_result[message.from_user.id]['Город'] = properties_data['data']['body']['header']
        search_result[message.from_user.id]['Отели'] = list()
        city_hotels: List[Any] = properties_data['data']['body']['searchResults']['results']

        if search_data[message.from_user.id]['search_command'] == 'Bestdeal':
            for i_hotel in city_hotels:
                price = i_hotel['ratePlan']['price']['exactCurrent']
                distance = float(re.match(r'\d+\.*,*\d*',
                                 i_hotel['landmarks'][0]['distance']).group().replace(',', '.'))
                if (price <= search_data[message.from_user.id]['max_price']) and (
                    distance <= search_data[message.from_user.id]['max_distance']):  # noqa: E125
                    hotel_info_filling(message, i_hotel)
                    if len(search_result[message.from_user.id]['Отели']) == search_data[message.from_user.id]['hotels_number']:
                        break
            search_result[message.from_user.id]['Отели'] = sorted(search_result[message.from_user.id]['Отели'],
                                                                  key=itemgetter('От центра', 'Цена, $'))

        else:
            for count, i_hotel in enumerate(city_hotels, 1):
                hotel_info_filling(message, i_hotel)
                if count == search_data[message.from_user.id]['hotels_number']:
                    break

        search_result_output(message)
    else:
        end_searching_error_text = 'Попробуйте подождать и попробовать снова.'
        hotels_bot.send_message(message.from_user.id, end_searching_error_text)


def city_definition(message: types.Message) -> None:
    """
    Функция принимает ответ пользователя и фиксирует наименование города
    и его destinationID в словаре search_data.
    В начале процесса отправляется запрос к API Hotels.com.
    В случае, если запрос к API будет неуспешным, пользователю в чат будет выведено соответствующее сообщение и
    процесс работы поисковой функции будет прекращён.
    В случае успешного запроса функция проводит обработку данных и создаёт виртуальную клавиатуру, с помощью
    которой пользователю предлагается ответить на следующий вопрос.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :raises ValueError: если код ответа не равен 200, вызывается исключение;
        обработка: пользователю в чате присылается сообщение об ошибке

    :raises TypeError: если от сервера приходит некорректный ответ, из-за чего сбивается путь поиска
        данных в полученном словаре;
        обработка: пользователю в чате присылается сообщение об ошибке, работа команды прекращается

    :raises IndexError: если пользователь некорректно ввёл название города (или такого города не существует);
        обработка: пользователю в чате присылается сообщение о некорректном вводе и просьба повторить ввод.

    """
    search_data[message.from_user.id].setdefault('city', message.text)

    location_url_part = '/locations/v2/search/'
    querystring = {"query": search_data[message.from_user.id]['city'], "locale": "ru_RU", "currency": "USD"}
    location_error_text = ('Что-то не так с ответом сервера по запросу локации...',
                           'Попробуйте подождать и попробовать снова.')
    location_data = get_request_data(message, location_url_part, querystring, location_error_text)
    try:
        destination_id = location_data['suggestions'][0]['entities'][0]['destinationId']
    except TypeError:
        error_text = ('От сервера пришёл некорректный ответ.\n'
                      'Пожалуйста, попробуйте снова, начав с ввода команды или /help')
        hotels_bot.send_message(message.from_user.id, error_text)
    except IndexError:
        error_text = ('Некорректный ввод.\n'
                      'Пожалуйста, попробуйте ввести название города снова')
        hotels_bot.send_message(message.from_user.id, error_text)
        hotels_bot.register_next_step_handler(message.from_user.id, city_definition)
    else:
        search_data[message.from_user.id].setdefault('destination_id', destination_id)
        keyboard = get_keyboard()
        hotels_bot.send_message(message.from_user.id, 'Сколько отелей показать?', reply_markup=keyboard)


@hotels_bot.callback_query_handler(func=lambda call: isinstance(call, types.CallbackQuery) is True)
def set_hotels_number(call: types.CallbackQuery) -> None:
    """
    Функция-обработчик обратного вызова, фиксирует в словаре search_data количество отелей,
    информацию по которым нужно будет найти.
    Принимает ответ, отправленный пользователем с помощью виртуальной клавиатуры, созданной в
    функции city_definition().
    В конце работы направляет к следующему обработчику сообщений - set_dates().

    :param call: объект ответа от кнопки на виртуальной клавиатуре
    :type call: telebot.types.CallbackQuery
    """
    search_data[call.from_user.id].setdefault('hotels_number', int(call.data))
    dates_question = ('Укажите даты заезда-выезда (формат: гггг-мм-дд - гггг-мм-дд).\n'
                      'Например 2022-10-15 - 2022-10-21')
    hotels_bot.send_message(call.from_user.id, dates_question)
    hotels_bot.register_next_step_handler(call.message, set_dates)


def set_dates(message: types.Message) -> None:
    """
    Функция принимает ответ пользователя и фиксирует даты пребывания в отеле, а также отдельно дату заезда и
    дату выезда из отеля, количество дней пребывания. Данные вносятся в словарь search_data.
    Исключение вызывается в случае, если пользователь внёс некорректные данные; обрабатывается
    уведомлением пользователя об ошибке ввода и запросом нового ввода.
    В конце работы направляет к следующему обработчику сообщений - set_photo_need_and_search().

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :raises ValueError: если даты введены некорректно;
        обработка: пользователю в чате присылается сообщение об ошибке с запросом повторного ввода.
    """
    dates = message.text.split(' - ')
    try:
        check_in = datetime.strptime(dates[0], '%Y-%m-%d')
        check_out = datetime.strptime(dates[1], '%Y-%m-%d')
        if check_out >= check_in:
            days_of_stay = days_calculation(check_in, check_out)
            search_data[message.from_user.id].setdefault('dates',
                                                         {'dates_of_stay': message.text,
                                                          'check_in': dates[0],
                                                          'check_out': dates[1],
                                                          'days_of_stay': days_of_stay})
            photo_question = ('Показывать ли фото для каждого отеля (да/нет)?',
                              'Если да, то сколько (через пробел, макс.фото = 6)?',
                              'Например:\nНет\n*или*\nДа 5')
            hotels_bot.send_message(message.from_user.id, '\n'.join(photo_question))
            hotels_bot.register_next_step_handler(message, set_photo_need_and_search)
    except ValueError:
        hotels_bot.send_message(message.from_user.id, 'Даты введены некорректно. Попробуйте снова.')
        hotels_bot.register_next_step_handler(message, set_dates)


def set_photo_need_and_search(message: types.Message) -> None:
    """
    Функция принимает и фиксирует ответ пользователя о необходимости вывода фотографий, а также об их количестве.
    Данные вносятся в словарь search_data.
    Исключение вызывается в случае, если пользователь внёс некорректные данные; обрабатывается
    уведомлением пользователя об ошибке ввода и запросом нового ввода.
    Если первая команда пользователя была "bestdeal", то в конце работы функция направляет к следующему
    обработчику сообщений - distance_definition().

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :raises ValueError: если ответ по фотографиям введён некорректно;
        обработка: пользователю в чате присылается сообщение об ошибке с запросом повторного ввода.
    """
    photo_need = message.text.split()
    try:
        if len(photo_need) == 1 and photo_need[0].lower() == 'нет':
            search_data[message.from_user.id].setdefault('photo_number', 'none')
        elif len(photo_need) == 2 and int(photo_need[1]) <= 6:
            search_data[message.from_user.id].setdefault('photo_number', int(photo_need[1]))
        else:
            raise ValueError
    except ValueError:
        error_text = 'Что-то не так. Введите ответ как показано в примере выше'
        hotels_bot.send_message(message.from_user.id, error_text)
        hotels_bot.register_next_step_handler(message, set_photo_need_and_search)
    else:
        if search_data[message.from_user.id]['search_command'] == 'Bestdeal':
            distance_question = ('Введите предельное расстояние отеля от центра города (в км)',
                                 'Например:\n5\n*или*\n9,3')
            hotels_bot.send_message(message.from_user.id, '\n'.join(distance_question))
            hotels_bot.register_next_step_handler(message, distance_definition)
        else:
            hotels_bot.send_message(message.from_user.id, 'Приступаю к поиску')
            search_for_matches(message)


def distance_definition(message: types.Message) -> None:
    """
    Функция принимает ответ пользователя о максимальном расстоянии отеля от центра города.
    Данные вносятся в словарь search_data.
    Исключение вызывается в случае, если пользователь внёс некорректные данные; обрабатывается
    уведомлением пользователя об ошибке ввода и запросом нового ввода.
    В конце работы функция направляет к следующему обработчику сообщений - price_definition().

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :raises ValueError: если значение расстояния введено некорректно;
        обработка: пользователю в чате присылается сообщение об ошибке с запросом повторного ввода.
    """
    try:
        max_distance = float((message.text.replace(',', '.')))
    except ValueError:
        error_text = 'Что-то не так. Введите ответ как показано в примере выше'
        hotels_bot.send_message(message.from_user.id, error_text)
        hotels_bot.register_next_step_handler(message, distance_definition)
    else:
        search_data[message.from_user.id].setdefault('max_distance', max_distance)
        price_question = ('Введите максимальную стоимость номера за одну ночь (в $)',
                          'Например:\n50\n*или*\n220,5')
        hotels_bot.send_message(message.from_user.id, '\n'.join(price_question))
        hotels_bot.register_next_step_handler(message, price_definition)


def price_definition(message: types.Message) -> None:
    """
    Функция принимает ответ пользователя о максимальной цене номера отеля.
    Данные вносятся в словарь search_data.
    Исключение вызывается в случае, если пользователь внёс некорректные данные; обрабатывается
    уведомлением пользователя об ошибке ввода и запросом нового ввода.
    В конце работы функция вызывает search_for_matches(), а та занимается поиском и выводом информации по найденным отелям.

    :param message: сообщение пользователя
    :type message: telebot.types.Message

    :raises ValueError: если значение расстояния введено некорректно;
        обработка: пользователю в чате присылается сообщение об ошибке с запросом повторного ввода.
    """
    try:
        max_price = float((message.text.replace(',', '.')))
    except ValueError:
        error_text = 'Что-то не так. Введите ответ как показано в примере выше'
        hotels_bot.send_message(message.from_user.id, error_text)
        hotels_bot.register_next_step_handler(message, price_definition)
    else:
        search_data[message.from_user.id].setdefault('max_price', max_price)
        hotels_bot.send_message(message.from_user.id, 'Приступаю к поиску')
        search_for_matches(message)


def saving_search_request(user_id: str) -> None:
    """
    Функция сохраняет поисковые данные из словарей search_data и search_result в файл search_requests.json.
    В полученном словаре данные по каждому пользователю распределены по датам и времени поискового запроса.

    Словарь каждого пользователя хранит не более 5 последних запросов. В случае, когда в словаре
    достигается этот предел, для предотвращения переполнения словаря удаляется самый ранний по дате запрос,
    после чего добавляется новый.

    :param user_id: ID пользователя, по которому будет записан поисковый запрос
    :type user_id: str
    """
    with open('search_requests.json', 'r', encoding='utf-8') as req_file:
        all_requests_data = json.load(req_file)

        if user_id not in all_requests_data:
            all_requests_data[user_id] = dict()

        if len(all_requests_data[user_id]) == 5:
            for count, search_date in enumerate(all_requests_data[user_id], 1):
                if count == 1:
                    all_requests_data[user_id].pop(search_date)
                    break

        new_request_data = dict()
        current_date = str(datetime.now()).partition('.')[0]

        new_request_data[current_date] = {
            'Команда поиска': search_data[int(user_id)]['search_command'],
            'Даты пребывания': search_data[int(user_id)]['dates']['dates_of_stay']
        }
        if search_data[int(user_id)]['search_command'] == 'Bestdeal':
            new_request_data[current_date].update(
                {
                    'Макс. расстояние от центра': '{value} км'.format(
                                                  value=search_data[int(user_id)]['max_distance']),
                    'Макс. цена, $': search_data[int(user_id)]['max_price']
                }
            )
        new_request_data[current_date].update(search_result[int(user_id)])
        all_requests_data[user_id].update(new_request_data)
        with open('search_requests.json', 'w', encoding='utf-8') as req_file:
            json.dump(all_requests_data, req_file, indent=4, ensure_ascii=False)
