from telebot import types  # noqa: D100


def get_keyboard() -> types.InlineKeyboardMarkup:
    """
    Функция, создающая виртуальную клавиатуру для удобства ввода пользователя.
    Создаётся клавиатура 3х3 с числами от 1 до 9.

    :return: keyboard
    :rtype: telebot.types.InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keys = [types.InlineKeyboardButton(text=str(number), callback_data=str(number))
            for number in range(1, 10)]
    keyboard.add(*keys)
    return keyboard
