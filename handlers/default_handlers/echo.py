"""
Обработчик НЕИЗВЕСТНЫХ КОМАНД для RelaxMassageBot.

Реагирует ТОЛЬКО на команды /команда которые не зарегистрированы:
- Игнорирует текст кнопок (записаться, прайс, история)
- Игнорирует FSM-состояния (waiting_*)
- Игнорирует известные команды (/start, /help, /history)
"""

from telebot.types import Message
from loader import bot
from keyboards.reply.reply_button import get_main_menu


def is_known_command(message: Message) -> bool:
    """Проверяет, является ли сообщение известной командой"""
    text = message.text or ''

    # Известные команды
    known_commands = ['/start', '/help', '/history']
    if text.startswith(tuple(known_commands)):
        return True

    # Reply-кнопки (игнорируем)
    button_texts = [
        'записаться', 'прайс', 'история', 'редактировать время'
    ]
    if any(text.lower() in btn for btn in button_texts):
        return True

    # FSM-состояния (игнорируем)
    if bot.get_state(message.from_user.id, message.chat.id):
        return True

    return False


@bot.message_handler(func=lambda m: m.text and m.text.startswith('/') and not is_known_command(m))
def handle_unknown_command(message: Message) -> None:
    """
    Обрабатывает ТОЛЬКО неизвестные команды /команда

    ✅ /start → обрабатывается start.py
    ✅ /help → обрабатывается help.py
    ✅ /random → echo.py (НЕИЗВЕСТНАЯ)
    ✅ "записаться" → start.py (reply-кнопка)
    ✅ В FSM состоянии → игнорируется
    """
    bot.reply_to(
        message,
        "❓ <b>Неизвестная команда</b>\n\n"
        "📋 Доступные команды:\n"
        "• /start - Главное меню\n"
        "• /history - История записей\n"
        "• /help - Справка\n\n"
        "<i>👆 Используйте кнопки меню!</i>",
        reply_markup=get_main_menu(message.from_user.id),
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and not is_known_command(m))
def handle_unknown_text(message: Message) -> None:
    """
    Обрабатывает ТОЛЬКО неизвестный текст (НЕ команды)

    ✅ "привет" → echo.py
    ✅ "что делаешь" → echo.py
    ❌ "записаться" → start.py (reply-кнопка)
    ❌ В FSM состоянии → игнорируется
    """
    bot.reply_to(
        message,
        "❓ Не понял сообщение.\n\n"
        "👆 Используйте кнопки меню или /start",
        reply_markup=get_main_menu(message.from_user.id)
    )
