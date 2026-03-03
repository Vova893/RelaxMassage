"""
✅ 🛠 Админская логика: календарь + управление слотами
"""

from __future__ import annotations
from telebot.types import CallbackQuery
from loader import bot
from datetime import datetime, date
from database.database import (DateBlock, Booking, is_admin, get_detailed_slot_status,
                               set_time_slot_availability, get_available_slots, get_slot_status_text)
from keyboards.inline.inline_admin import get_time_management_menu


def show_admin_clients(message):
    """📋 Показать админу ВСЕ записи с деталями"""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа!")
        return

    try:
        today = date.today()  # ✅ Сегодняшняя дата

        # Получаем ВСЕ активные записи (не отмененные)
        # ✅ ФИЛЬТР: только сегодняшние и будущие записи!
        active_bookings = Booking.select().where(
            Booking.is_cancelled == False,
            Booking.book_date >= today  # ✅ НЕ показываем прошедшие!
        ).order_by(Booking.book_date.asc(), Booking.time_slot.asc())

        if not active_bookings:
            text = "📝 <b>Пока нет активных записей!</b>"
        else:
            text = "📋 <b>Все активные записи:</b>\n\n"
            for booking in active_bookings:
                # Форматируем каждую запись
                text += (
                    f"🆔 <b>Запись №{booking.id}</b>\n"
                    f"📅 <b>{booking.book_date}</b> | 🕐 <b>{booking.time_slot}</b>\n"
                    f"💆 <b>{booking.service}</b>\n"
                    f"👤 <code>{booking.user_name}</code>\n"
                    f"📱 <code>{booking.phone}</code>\n\n"
                )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=None,
            parse_mode='HTML'
        )

    except Exception as e:
        # print(f"❌ Admin clients error: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки записей!")


def _show_admin_slots(call: CallbackQuery, date_str: str) -> None:
    """🕐 Админ: показать слоты"""

    # ✅ ИСПРАВЛЯЕМ срез для admin_slots_2026-02-28
    if call.data.startswith('admin_slots_'):
        date_str = call.data.replace('admin_slots_', '')  # Убираем префикс полностью

    day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    markup = get_time_management_menu(date_str)

    bot.edit_message_text(
        get_detailed_slot_status(day_date),
        call.message.chat.id, call.message.message_id,
        reply_markup=markup, parse_mode='HTML'
    )


def _admin_toggle_slot(call: CallbackQuery) -> None:
    """🔄 Админ toggle слота"""
    parts = call.data.split('_')  # toggle_slot_2026-03-02_09:00
    if len(parts) >= 4:
        # ✅ ПРАВИЛЬНЫЙ разбор: ['toggle', 'slot', '2026-03-02', '09:00']
        date_str, time_slot = parts[2], parts[3]

        book_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        current_available = get_available_slots(book_date)
        new_status = time_slot not in current_available

        set_time_slot_availability(book_date, time_slot, new_status)

        markup = get_time_management_menu(date_str)
        status_text = get_slot_status_text(book_date)
        change_text = f"\n✅ <b>{time_slot}</b> {'включен' if new_status else 'отключен'}"

        bot.edit_message_text(
            status_text + change_text,
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode='HTML'
        )

        # + "\n⭕ Доступно | ✅ Отключено"
        # set_time_slot_availability(book_date, time_slot, new_status)

        # markup = get_time_management_menu(date_str)
        # status_text = get_slot_status_text(book_date)
        # change_text = f"\n✅ <b>{time_slot}</b> {'отключен' if new_status else 'включен'}"
        #
        # bot.edit_message_text(
        #     status_text + change_text,
        #     call.message.chat.id, call.message.message_id,
        #     reply_markup=markup, parse_mode='HTML'
        # )


@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_date_'))
def handle_toggle_date(call: CallbackQuery):
    """🔒 Вкл/выкл всю дату"""
    try:
        date_str = call.data.replace('toggle_date_', '')
        day_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Переключаем статус
        existing_block = DateBlock.get_or_none(DateBlock.block_date == day_date)
        if existing_block:
            existing_block.delete_instance()  # Удаляем блокировку
            status = "✅ Дата включена!"
        else:
            DateBlock.create(block_date=day_date)
            status = "🔒 Дата отключена!"

        # Обновляем меню
        markup = get_time_management_menu(date_str)
        text = f"📅 <b>{date_str}</b>\n\n{status}"

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=markup, parse_mode='HTML')

    except Exception as e:
        # print(f"❌ Toggle date error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_slot_'))
def handle_toggle_slot(call: CallbackQuery):
    """🔄 Админ: вкл/выкл отдельный слот времени"""
    try:
        _admin_toggle_slot(call)  # Вызываем вашу функцию
        bot.answer_callback_query(call.id)  # ✅ Подтверждаем клик
    except Exception as e:
        print(f"❌ Toggle slot error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
