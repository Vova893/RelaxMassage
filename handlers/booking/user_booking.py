"""
✅ 👥 Пользовательская логика записи
Календарь → Дата → Время → Услуга → ФИО+Телефон
"""

from __future__ import annotations
from telebot.types import CallbackQuery
from loader import bot
from database.database import get_available_slots
from keyboards.inline.date_menu import (
    get_month_calendar, get_time_menu, get_services_menu
)
from states.states import UserStates
from datetime import datetime, date, timedelta
from typing import List


def handle_user_callback(call: CallbackQuery) -> None:
    """Обработка callback для пользователей"""

    # 📅 Календарь
    if call.data == 'calendar':
        markup = get_month_calendar()
        bot.edit_message_text(
            "📅 <b>ЗАПИСЬ НА МАССАЖ</b>\n🟢 = Свободно | 🔴 = Занято",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode='HTML'
        )
        return

    # 📅 Навигация по месяцам
    if call.data.startswith('month_'):
        try:
            month_num: int = int(call.data[6:])
            markup = get_month_calendar(selected_month=month_num)
            bot.edit_message_text(
                "📅 Выберите дату:",
                call.message.chat.id, call.message.message_id,
                reply_markup=markup, parse_mode='HTML'
            )
        except ValueError:
            pass
        return

    # 📅 Выбор даты (date_20-02-2026)
    if call.data.startswith('date_') and len(call.data) > 11:
        date_str: str = call.data[5:]
        try:
            book_date: date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slots: List[str] = get_available_slots(book_date)

            if slots:
                bot.edit_message_text(
                    "🕐 Выберите время:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=get_time_menu(date_str, slots)
                )
                bot.set_state(
                    call.from_user.id,
                    UserStates.waiting_time,
                    call.message.chat.id
                )
            else:
                bot.answer_callback_query(call.id, "❌ Нет слотов", show_alert=True)
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Ошибка даты", show_alert=True)
        return

    # 🕐 Сегодня/Завтра
    if call.data == 'date_today':
        handle_date_selection(call, date.today())
    elif call.data == 'date_tomorrow':
        handle_date_selection(call, date.today() + timedelta(days=1))

    # 🕐 Выбор времени
    if call.data.startswith('time_'):
        date_str, time_slot = call.data[5:].rsplit('_', 1)
        bot.edit_message_text(
            f"✅ <b>Дата:</b> {date_str}\n🕐 <b>Время:</b> {time_slot}\n💆 Выберите услугу:",
            call.message.chat.id, call.message.message_id,
            reply_markup=get_services_menu(), parse_mode='HTML'
        )
        bot.set_state(call.from_user.id, UserStates.waiting_service, call.message.chat.id)

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['selected_date'] = date_str
            data['selected_time'] = time_slot
        return

    # 💆 Выбор услуги
    if call.data.startswith('service_'):
        service: str = call.data[8:]
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data['selected_service'] = service

        bot.edit_message_text(
            f"💆 <b>Предзаказ:</b>\n📅 {data['selected_date']}\n"
            f"🕐 {data['selected_time']}\n💼 {service}\n\n"
            f"👤 <b>ФИО:</b>\n📞 <b>Телефон:</b>",
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML'
        )
        bot.set_state(call.from_user.id, UserStates.waiting_name_phone, call.message.chat.id)
        return


def handle_date_selection(call: CallbackQuery, book_date: date) -> None:
    """Обработка быстрого выбора даты"""
    slots = get_available_slots(book_date)
    date_str = str(book_date)

    if slots:
        bot.edit_message_text(
            f"🕐 {'Сегодня' if book_date == date.today() else 'Завтра'}- выберите время:",
            call.message.chat.id, call.message.message_id,
            reply_markup=get_time_menu(date_str, slots)
        )
        bot.set_state(call.from_user.id, UserStates.waiting_time, call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Нет слотов", show_alert=True)
