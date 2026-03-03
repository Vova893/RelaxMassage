"""
📅 date_menu.py - ПОЛЬЗОВАТЕЛЬСКИЙ календарь (🔴 прошедшие дни!)

✅ Показывает:
   🔴 Прошедшие дни (недоступны)
   📅 Сегодня (доступно)
   🟢 Будущие дни (по слотам)
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional, Tuple
from datetime import date, timedelta
from database.database import get_available_slots
from config_data.settings import MAX_BOOKING_DAYS, SERVICES_MAP


def get_month_calendar(selected_month: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    📅 ПОЛНОЦЕННЫЙ календарь для ПОЛЬЗОВАТЕЛЕЙ

    Логика цветовой индикации:
    ✅ 🔴 ПРОШЕДШИЕ ДНИ (< today)
    ✅ 📅 СЕГОДНЯ (== today)
    ✅ 🟢 БУДУЩИЕ С СЛОТАМИ (>0 слотов)
    ✅ 🔴 БУДУЩИЕ БЕЗ СЛОТОВ (0 слотов)
    """
    today = date.today()

    # 📅 Текущий месяц или выбранный
    if selected_month:
        year = today.year if selected_month >= today.month else today.year + 1
        first_day = date(year, selected_month, 1)
    else:
        first_day = date(today.year, today.month, 1)

    # 📊 Последний день месяца
    next_month = first_day.month % 12 + 1
    last_day = date(first_day.year, next_month, 1) - timedelta(days=1)

    markup = InlineKeyboardMarkup(row_width=7)

    # 🎯 Заголовок месяца
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
        7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }

    prev_month_cb = f'month_{first_day.month - 1 if first_day.month > 1 else 12}'
    next_month_cb = f'month_{next_month}'

    header_row = [
        InlineKeyboardButton("◀️", callback_data=prev_month_cb),
        InlineKeyboardButton(
            f"{month_names[first_day.month]} {first_day.year}",
            callback_data='calendar_header'
        ),
        InlineKeyboardButton("▶️", callback_data=next_month_cb)
    ]
    markup.row(*header_row)

    # 📅 Дни недели
    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    markup.row(*[InlineKeyboardButton(day, callback_data='week_header') for day in week_days])

    # 🎯 ДНИ МЕСЯЦА с цветовой индикацией
    current_row = []
    weekday = first_day.weekday()  # 0=Пн, 6=Вс

    # Пустые ячейки начала месяца
    for _ in range(weekday):
        current_row.append(InlineKeyboardButton(" ", callback_data='empty'))

    # 📊 Все дни месяца
    for day_num in range(1, last_day.day + 1):
        day_date = date(first_day.year, first_day.month, day_num)
        status_emoji, callback_data = get_user_day_status(day_date)

        # ✅ Кнопка дня (только если доступна)
        if status_emoji != "🔴" or day_date == today:  # Прошедшие недоступны
            btn = InlineKeyboardButton(
                f"{status_emoji} {day_num}",
                callback_data=callback_data
            )
        else:
            btn = InlineKeyboardButton(
                f"{status_emoji} {day_num}",
                callback_data='past_day'  # Отключаем клик
            )

        current_row.append(btn)

        # ➡️ Новая строка каждые 7 дней
        if len(current_row) == 7:
            markup.row(*current_row)
            current_row = []

    # 📦 Последняя строка
    if current_row:
        while len(current_row) < 7:
            current_row.append(InlineKeyboardButton(" ", callback_data='empty'))
        markup.row(*current_row)

    # # 🚀 Быстрые кнопки
    # markup.row(
    #     types.InlineKeyboardButton("📅 Сегодня", callback_data='date_today'),
    #     types.InlineKeyboardButton("📆 Завтра", callback_data='date_tomorrow')
    # )
    markup.row(
        InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')
    )

    return markup


def get_user_day_status(day_date: date) -> Tuple[str, str]:
    """
    🎨 Статус дня для ПОЛЬЗОВАТЕЛЬСКОГО календаря

    Логика (приоритет сверху вниз):
    1. 🔴 ПРОШЕДШИЕ ДНИ (< today)
    2. 📅 СЕГОДНЯ (== today)
    3. 🟢 БУДУЩИЕ С СЛОТАМИ (>0)
    4. 🔴 БУДУЩИЕ БЕЗ СЛОТОВ (0)
    """
    today = date.today()
    max_date = today + timedelta(days=MAX_BOOKING_DAYS)

    # 1. 🔴 ПРОШЕДШИЕ ДНИ
    if day_date < today:
        return "🔴", 'past_day'

    # 2. 📅 СЕГОДНЯ
    if day_date == today:
        return "📅", f"date_{day_date.strftime('%Y-%m-%d')}"

    # 3. 🔴 СЛИШКОМ ДАЛЕКО (> MAX_BOOKING_DAYS)
    if day_date > max_date:
        return "🔴", 'too_far_day'

    # 4. БУДУЩИЕ ДНИ по слотам
    slots = get_available_slots(day_date)
    if len(slots) > 0:
        return "🟢", f"date_{day_date.strftime('%Y-%m-%d')}"
    else:
        return "🔴", 'no_slots_day'


def get_time_menu(date_str: str, available_slots: List[str]) -> InlineKeyboardMarkup:
    """
    🕐 Меню времени ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
    ✅ 3 СЛОТА В СТРОКЕ: 09:00 10:00 11:00
                         12:00 13:00 14:00
    """
    markup = InlineKeyboardMarkup(row_width=3)  # ✅ 3 в строке!

    # Добавляем по 3 кнопки в строку
    for i in range(0, len(available_slots), 3):
        row = available_slots[i:i + 3]
        row_buttons = [
            InlineKeyboardButton(
                slot, callback_data=f'time_{date_str}_{slot}'
            ) for slot in row
        ]
        markup.row(*row_buttons)

    # Кнопки навигации
    markup.row(
        InlineKeyboardButton("🔙 Календарь", callback_data='calendar'),
        InlineKeyboardButton("🏠 Меню", callback_data='main_menu')
    )
    return markup


def get_services_menu(page: int = 0) -> InlineKeyboardMarkup:
    """💆 Меню услуг ПАГИНАЦИЯ: 10 услуг на страницу"""
    markup = InlineKeyboardMarkup(row_width=1)

    # 10 услуг на страницу
    start_idx = page * 10
    end_idx = start_idx + 10
    page_services = list(SERVICES_MAP.items())[start_idx:end_idx]

    # Добавляем 10 кнопок
    for code, name in page_services:
        markup.add(InlineKeyboardButton(name, callback_data=f'service_{code}'))

    # ✅ Навигация страниц
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f'services_{page - 1}'))
    if end_idx < len(SERVICES_MAP):
        nav_row.append(InlineKeyboardButton("Вперед ▶️", callback_data=f'services_{page + 1}'))

    if nav_row:
        markup.row(*nav_row)

    # Нижние кнопки
    markup.row(
        InlineKeyboardButton("🔙 Назад", callback_data='back_to_time'),
        InlineKeyboardButton("🏠 Меню", callback_data='main_menu')
    )
    return markup


def get_name_phone_keyboard() -> InlineKeyboardMarkup:
    """👤📞 ПЕРВЫЙ этап - ФИО + Телефон"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("👤 Ввести ФИО", callback_data='enter_your_full_name'),
        InlineKeyboardButton("🚫 Отмена", callback_data='cancellation')
    )
    return markup


def get_phone_keyboard() -> InlineKeyboardMarkup:
    """📞 2-й этап - только телефон + отмена"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📞 Ввести телефон", callback_data='enter_a_phone'),
        InlineKeyboardButton("🚫 Отмена", callback_data='cancellation')
    )
    return markup


def get_history_menu(bookings):
    """Клавиатура для истории бронирований"""
    markup = InlineKeyboardMarkup(row_width=2)

    if not bookings:
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        return markup

    # Кнопки отмены только для активных броней
    for booking in bookings[:5]:
        markup.add(
            InlineKeyboardButton(
                f"❌ Отменить #{booking.id}",
                callback_data=f"cancel_{booking.id}"
            )
        )

    markup.row(
        InlineKeyboardButton("📜 Все брони", callback_data="history_all"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return markup
