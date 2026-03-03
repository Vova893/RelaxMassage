from loader import bot
from config_data.config import ADMIN_ID


def booking_notification(booking):
    """
    Уведомление админу о новой записи
    :param booking: Новая запись
    :return: None
    """

    text = (f'<b>Новая запись!</b>\n\n'
            f"✅ Бронь №{booking.id}\n"
            f"📅 {booking.book_date} {booking.time_slot}\n"
            f"💆 {booking.service}\n"
            f"👤 {booking.user_name}\n"
            f"📱 <code>{booking.phone or "Не указан"}</code>")

    try:
        for admin_id in ADMIN_ID:
            bot.send_message(admin_id, text, parse_mode='HTML')

    except Exception as e:
        print(f'Ошибка уведомления админа: {e}')
