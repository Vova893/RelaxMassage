"""
Reply-клавиатуры для RelaxMassageBot.

get_main_menu(): главное меню с 3 кнопками + 4-я для админов
"""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database.database import is_admin


def get_main_menu(telegram_id: int) -> ReplyKeyboardMarkup:
    """Главное меню: 3 кнопки + админская кнопка"""
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        row_width=1
    )

    # Базовые кнопки для всех
    markup.add(KeyboardButton('📅 Записаться на массаж'))
    markup.add(KeyboardButton('💰 Прайс услуг'))
    # if not is_admin(telegram_id):
    markup.add(KeyboardButton('📋 История записи'))

    # Админская кнопка (только для ADMIN_ID)
    if is_admin(telegram_id):
        markup.add(KeyboardButton('🛠 Редактировать время'))
        markup.add(KeyboardButton('📋 Посмотреть записи'))
    return markup
