"""
Обработчик команды /help для RelaxMassageBot.

Показывает справку по командам и reply-кнопкам.
"""

from telebot.types import Message
from loader import bot
from keyboards.reply.reply_button import get_main_menu


@bot.message_handler(commands=['help'])
def bot_help(message: Message) -> None:
    """Отправляет справку пользователю"""
    text = """
🤖 <b>RelaxMassageBot</b> - запись на массаж

<b>📋 Команды:</b>
/start - Главное меню 
/help - Справка

<b>⌨️ Reply кнопки:</b>
📅 Записаться на массаж
💰 Прайс услуг
📋 История записи
🛠 Редактировать время (только админы)

<b>📅 Запись:</b>
1. Выберите дату (календарь)
2. Выберите время (зеленые слоты)
3. Выберите услугу
4. Введите ФИО + телефон
"""
    bot.reply_to(
        message,
        text,
        reply_markup=get_main_menu(message.from_user.id),
        parse_mode='HTML'
    )
