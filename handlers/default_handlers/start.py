"""
Обработчики команд /start и reply-кнопок главного меню.

Функции:
- Регистрация пользователя в БД
- Логирование команды /start
- Главное меню с 4 кнопками для админов
- Быстрый доступ к календарю, прайсу, истории для пользователей
"""

from telebot.types import Message
from loader import bot, bots_abilities
from database.database import register_user_if_not_exists, log_action, is_admin
from keyboards.reply.reply_button import get_main_menu
from keyboards.inline.date_menu import get_month_calendar
from handlers.booking.admin_handler import show_admin_clients
from config_data.settings import SERVICES_MAP


@bot.message_handler(commands=['start'])
def bot_start(message: Message) -> None:
    """Обработчик команды /start - главное меню"""
    user = register_user_if_not_exists(message.from_user)
    log_action(user, 'command_start')

    welcome_text = (
        f"🏆 Добро пожаловать в <b>RelaxMassageBot</b>, "
        f"{message.from_user.first_name or ''}!\n{bots_abilities}\n"
        "Выберите действие:"
    )

    reply_markup = get_main_menu(user.telegram_id)
    bot.reply_to(
        message,
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda m: 'записаться' in m.text.lower())
def handle_book(message: Message) -> None:
    """Обработчик кнопки 'Записаться' - показывает календарь"""
    markup = get_month_calendar()
    bot.send_message(
        message.chat.id,
        "📅 <b>Выберите дату:</b>\n\n"
        "🟢 = Есть свободное время\n"
        "🔴 = Все слоты заняты\n"
        "📅 = Сегодня",
        reply_markup=markup,
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda m: 'прайс' in m.text.lower())
def handle_price(message: Message) -> None:
    """Обработчик кнопки 'Прайс услуг'"""

    def format_services_map(services_map: dict) -> str:
        """🎨 Форматирует SERVICES_MAP для бота"""
        text = "💆 <b>ПРАЙС-ЛИСТ УСЛУГ:</b>\n\n"

        for code, service in services_map.items():
            # Добавляем эмодзи и нумерацию
            emoji = "🧿" if "Классический" in service else "💎" if "СПА" in service else "🍯" \
                if "Медовый" in service else "✨"
            text += f"{emoji} <code>{code}</code> {service}\n\n"

        return text

    # ✅ Использование:
    text = format_services_map(SERVICES_MAP)
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: 'история' in m.text.lower())
def handle_history(message: Message) -> None:
    """Обработчик кнопки 'История записи'"""
    from database.database import get_user_bookings
    bookings = get_user_bookings(message.from_user.id)

    if bookings:
        text = "📋 <b>Ваши активные записи:</b>\n\n"
        for b in bookings:
            text += (
                f"🗓 <b>{b.book_date}</b> {b.time_slot}\n"
                f"💆 {b.service}\n"
                f"👤 {b.user_name}\n\n"
            )
        from keyboards.inline.date_menu import get_history_menu
        markup = get_history_menu(bookings)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    else:
        bot.send_message(
            message.chat.id,
            "📭 У вас нет активных записей\n\n"
            "📅 <b>Запишитесь на массаж!</b>"
        )


@bot.message_handler(func=lambda m: 'посмотреть записи' in m.text.lower())
def handle_admin_clients(message):
    if is_admin(message.from_user.id):
        show_admin_clients(message)
