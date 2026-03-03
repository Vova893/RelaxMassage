"""
🚀 main_handler.py - TeleBot синтаксис (bot.answer_callback_query!)
"""

# from __future__ import annotations
from telebot.types import CallbackQuery
from loader import bot  # ✅ bot для bot.answer_callback_query()
from database.database import register_user_if_not_exists, is_admin, log_button_click, get_available_slots
from handlers.booking.admin_handler import _show_admin_slots, _admin_toggle_slot
from keyboards.reply.reply_button import get_main_menu
from keyboards.inline.date_menu import get_services_menu, get_time_menu
from states.states import UserStates
from datetime import date, timedelta, datetime
from config_data.settings import SERVICES_MAP


@bot.callback_query_handler(func=lambda call: not call.data == 'enter_your_full_name'
                                              and not call.data == 'enter_a_phone'
                                              and not call.data == 'cancellation'
                                              and not call.data.startswith('count_')
                                              and not call.data.startswith('cancel_')
                                              and not call.data.startswith('toggle_date_')
                                              and not call.data.startswith('toggle_slot_')
                                              and not call.data.startswith('services_')
                                              and not call.data == 'history_all'
                                              and not call.data == 'history_active')
def callback_router(call: CallbackQuery) -> None:
    """🚀 ГЛАВНЫЙ обработчик inline кнопок"""
    user = register_user_if_not_exists(call.from_user)
    log_button_click(user, call.data)

    # 🏠 Главное меню
    if call.data in ['main_menu', 'cancel']:
        bot.delete_state(user.telegram_id, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            "🏠 Главное меню:",
            reply_markup=get_main_menu(user.telegram_id)
        )
        bot.answer_callback_query(call.id)  # ✅ ПРАВИЛЬНО!
        return

    # 🚫 Недоступные дни
    if call.data in ['past_day', 'no_slots_day', 'too_far_day']:
        bot.answer_callback_query(call.id, "❌ День недоступен!", show_alert=True)
        return

    # 🛠 АДМИН
    if is_admin(user.telegram_id):
        if _handle_admin(call):
            bot.answer_callback_query(call.id)
            return

    # 👥 ПОЛЬЗОВАТЕЛЬ
    _handle_user(call)
    bot.answer_callback_query(call.id)  # ✅ ВСЕГДА в конце!


def _handle_admin(call: CallbackQuery) -> bool:
    """🛠 Админские функции"""
    # 📅 Админ календарь
    if call.data == 'admin_calendar':
        from keyboards.inline.inline_admin import get_admin_calendar_menu
        markup = get_admin_calendar_menu()
        bot.edit_message_text(
            "🛠 <b>Управление расписанием</b>\n🔴=Прошедшее | 🟢=Свободно",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode='HTML'
        )
        return True

    # 📅 Месяцы админ
    if call.data.startswith('admin_month_'):
        try:
            month = int(call.data.split('_')[-1])
            from keyboards.inline.inline_admin import get_admin_calendar_menu
            markup = get_admin_calendar_menu(selected_month=month)
            bot.edit_message_text(
                "🛠 Календарь:",
                call.message.chat.id, call.message.message_id,
                reply_markup=markup, parse_mode='HTML'
            )
        except:
            pass
        return True

    # 📅 Админ дата
    if call.data.startswith('admin_date_'):
        date_str = call.data[11:]
        from keyboards.inline.inline_admin import get_admin_date_menu
        markup = get_admin_date_menu(date_str)
        bot.edit_message_text(
            f"🛠 Управление: {date_str}",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode='HTML'
        )
        return True

    # 🕐 Админ слоты
    if call.data.startswith('admin_slots_'):
        date_str = call.data[11:]
        _show_admin_slots(call, date_str)
        return True

    # 🔄 Toggle слота
    if call.data.startswith('admin_toggle_'):
        _admin_toggle_slot(call)
        return True

    return False


def _handle_user(call: CallbackQuery) -> None:
    """👥 Пользовательские функции"""

    # 📅 Календарь
    if call.data == 'calendar':
        from keyboards.inline.date_menu import get_month_calendar
        markup = get_month_calendar()
        bot.edit_message_text(
            "📅 <b>ЗАПИСЬ НА МАССАЖ</b>\n🔴=Недоступно | 🟢=Свободно",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode='HTML'
        )
        return

    # 📅 Месяцы
    if call.data.startswith('month_'):
        try:
            month = int(call.data[6:])
            from keyboards.inline.date_menu import get_month_calendar
            markup = get_month_calendar(selected_month=month)
            bot.edit_message_text(
                "📅 Выберите дату:",
                call.message.chat.id, call.message.message_id,
                reply_markup=markup, parse_mode='HTML'
            )
        except:
            pass
        return

    # 📅 Быстрые даты
    if call.data == 'date_today':
        _user_select_date(call, date.today())
        return
    if call.data == 'date_tomorrow':
        _user_select_date(call, date.today() + timedelta(days=1))
        return

    # 📅 Дата из календаря
    if call.data.startswith('date_'):
        date_str = call.data[5:]
        _user_select_date(call, date_str)
        return

    # 🕐 Время
    if call.data.startswith('time_'):
        parts = call.data.split('_', 2)
        if len(parts) == 3:
            date_str, time_slot = parts[1], parts[2]
            _user_select_time(call, date_str, time_slot)
        return

    # 💆 Услуга
    if call.data.startswith('service_'):
        service = call.data[8:]
        _user_select_service(call, service)
        return


def _user_select_date(call: CallbackQuery, date_obj_or_str) -> None:
    """📅 → 🕐 Показать время"""
    if isinstance(date_obj_or_str, date):
        date_str = date_obj_or_str.strftime('%Y-%m-%d')
    else:
        date_str = date_obj_or_str

    try:
        book_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # print(f"🔍 DEBUG: date_str={date_str}, book_date={book_date}")
        slots = get_available_slots(book_date)
        # print(f"🔍 DEBUG: available_slots={slots}")

        time_markup = get_time_menu(date_str, slots)
        # print(f"🔍 DEBUG: time_markup={time_markup is not None}")

        if slots:
            bot.edit_message_text(
                f"🕐 <b>{date_str}</b> - выберите время:",
                call.message.chat.id, call.message.message_id,
                reply_markup=time_markup,  # get_time_menu(date_str, slots),
                parse_mode='HTML'
            )
            bot.set_state(call.from_user.id, UserStates.waiting_time, call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "❌ Нет слотов!", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


def _user_select_time(call: CallbackQuery, date_str: str, time_slot: str) -> None:
    """🕐 → 💆 Показать услуги"""
    bot.answer_callback_query(call.id)  # ✅ Обязательно!

    bot.edit_message_text(
        f"✅ <b>Дата:</b> {date_str}\n🕐 <b>Время:</b> {time_slot}\n💆 Выберите услугу:",
        call.message.chat.id, call.message.message_id,
        reply_markup=get_services_menu(),
        parse_mode='HTML'
    )
    bot.set_state(call.from_user.id, UserStates.waiting_service, call.message.chat.id)

    # 💾 Сохранить в storage
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['selected_date'] = date_str
        data['selected_time'] = time_slot


def _user_select_service(call: CallbackQuery, service: str) -> None:
    """💆 → 👤📞 Inline кнопки ПОЛЯ"""
    from keyboards.inline.date_menu import get_name_phone_keyboard

    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # ✅ ПРОВЕРКА данных перед использованием!
    with bot.retrieve_data(user_id, chat_id) as data:
        # Защита от KeyError
        if 'selected_date' not in data or 'selected_time' not in data:
            bot.answer_callback_query(call.id, "❌ Данные утеряны! Начните заново.", show_alert=True)
            bot.delete_state(user_id, chat_id)
            bot.send_message(chat_id, "🏠 Главное меню:", reply_markup=get_main_menu(user_id))
            return

        data['selected_service'] = service

        # ✅ Безопасное использование данных
        preview_text = (
            f"💆 <b>Предзаказ:</b>\n"
            f"📅 {data['selected_date']}\n"
            f"🕐 {data['selected_time']}\n"
            f"💼 {service}"
        )

    bot.edit_message_text(
        preview_text,
        chat_id,
        call.message.message_id,
        parse_mode='HTML'
    )

    # ✅ Inline клавиатура ПОЛЯ!
    bot.send_message(
        chat_id,
        "👇 <b>Нажмите на кнопку '👤 Ввести ФИО'\n"
        f"а затем укажите как вас зовут:</b>",
        reply_markup=get_name_phone_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('services_'))
def handle_services_pagination(call):
    """📄 Навигация по страницам услуг"""
    page = int(call.data.split('_')[1])
    markup = get_services_menu(page)
    bot.edit_message_text(
        "💆 <b>Выберите услугу:</b>\n<i>(страница {}/{})</i>".format(
            page + 1, (len(SERVICES_MAP) + 9) // 10
        ),
        call.message.chat.id, call.message.message_id,
        reply_markup=markup, parse_mode='HTML'
    )
