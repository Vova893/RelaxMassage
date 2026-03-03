"""
Утилита установки команд бота в меню Telegram.

Регистрирует команды: /start, /help
"""

from telebot.types import BotCommand
from config_data.config import DEFAULT_COMMANDS


def set_default_commands(bot) -> None:
    """Устанавливает команды бота в меню Telegram"""
    bot.set_my_commands([BotCommand(*cmd) for cmd in DEFAULT_COMMANDS])
