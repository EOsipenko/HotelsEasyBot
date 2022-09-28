from config import ORIGINAL_COMMANDS, hotels_bot  # noqa: D100

from telebot import types


@hotels_bot.message_handler(commands=['help'])
def helping(message: types.Message):
    """
    Функция - обработчик команды пользователя '/help'.
    Выводит пользователю список команд, с помощью которых можно обращаться к боту.

    :param message: сообщение пользователя
    :type message: telebot.types.Message
    """
    help_text = ['Доступны следующие команды:']
    help_text.extend(['/{command} - {description}'.format(command=command,
                     description=description)
                     for command, description in ORIGINAL_COMMANDS])
    hotels_bot.send_message(message.from_user.id, '\n'.join(help_text))
