"""
✅ АДМИНСКИЙ КАЛЕНДАРЬ - выбор дат для управления
Рабочий день / Выходной / Статистика
"""

from telebot.types import Message
from loader import bot
from database.database import is_admin
from keyboards.inline.inline_admin import get_admin_calendar_menu


@bot.message_handler(func=lambda m: m.text == '🛠 Редактировать время')
def handle_admin_calendar(message: Message) -> None:
    """Админ: Редактировать время → АДМИНСКИЙ КАЛЕНДАРЬ"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Нет доступа")
        return

    markup = get_admin_calendar_menu()
    bot.send_message(
        message.chat.id,
        "🛠 <b>УПРАВЛЕНИЕ РАБОТОЙ МАССАЖИСТА</b>\n\n"
        "📅 <b>Выберите день:</b>\n\n"
        "🟢 Рабочий день (доступно бронирование)\n"
        "🔴 Выходной день (недоступно)\n",
        reply_markup=markup,
        parse_mode='HTML'
    )
