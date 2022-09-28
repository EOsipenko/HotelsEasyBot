from config import ORIGINAL_COMMANDS  # noqa: D100

from telebot import TeleBot
from telebot.types import BotCommand


def set_default_commands(bot: TeleBot) -> None:
    """
    Функция устанавливает меню - список команд, через которых пользователь может работать
    с ботом.

    :param bot: бот, которому устанавливается список команд
    :type bot: telebot.TeleBot
    """
    bot.set_my_commands(
        [BotCommand(*command) for command in ORIGINAL_COMMANDS]
    )
