"""
🛠 inline_admin.py - ПОЛНОЦЕННЫЙ АДМИНСКИЙ КАЛЕНДАРЬ

✅ Показывает:
    Рабочий день (много свободно)
   🟡 Частично занят
   ❗️ Выходной/полностью занят
   📅 Сегодня (выделено)

✅ Навигация: ◀️ Пред.мес. | След.мес. ▶️
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from database.database import get_available_slots, DateBlock, Booking
from config_data.settings import WORK_HOURS


def get_admin_calendar_menu(
        selected_month: Optional[int] = None,
        current_date: Optional[date] = None
) -> InlineKeyboardMarkup:
    """
    📅 ПОЛНОЦЕННЫЙ админский календарь на месяц

    Args:
        selected_month: месяц (1-12), None=текущий
        current_date: текущая дата для выравнивания

    Returns:
        InlineKeyboardMarkup с датами + статусами
    """
    if current_date is None:
        current_date = date.today()

    # 📅 Определяем месяц
    if selected_month:
        year = current_date.year if selected_month >= current_date.month else current_date.year + 1
        first_day = date(year, selected_month, 1)
    else:
        first_day = date(current_date.year, current_date.month, 1)

    # 📊 Последний день месяца
    next_month = first_day.month % 12 + 1
    last_day = date(first_day.year, next_month, 1) - timedelta(days=1)

    markup = InlineKeyboardMarkup(row_width=7)

    # 🎯 Заголовок с навигацией
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }

    prev_month = first_day.month - 1 if first_day.month > 1 else 12
    next_month_num = next_month

    header_row = [
        InlineKeyboardButton("◀️", callback_data=f'admin_month_{prev_month}'),
        InlineKeyboardButton(
            f"{month_names[first_day.month]} {first_day.year}",
            callback_data='admin_calendar_header'
        ),
        InlineKeyboardButton("▶️", callback_data=f'admin_month_{next_month_num}')
    ]
    markup.row(*header_row)

    # 📅 Дни недели
    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    markup.row(*[InlineKeyboardButton(day, callback_data='admin_week_header')
                 for day in week_days])

    # 🎯 ДНИ МЕСЯЦА с цветовой индикацией
    current_row = []
    weekday = first_day.weekday()  # 0=Пн, 6=Вс

    # Пустые ячейки начала месяца
    for i in range(weekday):
        current_row.append(InlineKeyboardButton(" ", callback_data='admin_empty'))

    # 📊 Все дни месяца
    for day_num in range(1, last_day.day + 1):
        day_date = date(first_day.year, first_day.month, day_num)

        # ✅ Статус дня (🟢🟡🔴)
        status_emoji, day_text = get_admin_day_status(day_date)

        # 📅 Callback для дня
        callback_data = f'admin_date_{day_date.strftime("%Y-%m-%d")}'

        # ✅ Кнопка дня
        button_text = f"{status_emoji} {day_num}" if status_emoji != '📅' else f"📅 {day_num}"
        btn = InlineKeyboardButton(button_text, callback_data=callback_data)

        current_row.append(btn)

        # ➡️ Новая строка каждые 7 дней
        if len(current_row) == 7:
            markup.row(*current_row)
            current_row = []

    # 📦 Последняя неполная строка
    if current_row:
        # Заполняем пустыми ячейками
        while len(current_row) < 7:
            current_row.append(InlineKeyboardButton(" ", callback_data='admin_empty'))
        markup.row(*current_row)

    # # 🚀 Быстрые кнопки
    # markup.row(
    #     types.InlineKeyboardButton("📅 Сегодня", callback_data='admin_date_today'),
    #     types.InlineKeyboardButton("📆 Завтра", callback_data='admin_date_tomorrow')
    # )
    markup.row(
        InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')
    )

    return markup


def get_admin_day_status(day_date: date) -> Tuple[str, str]:
    """
    🎨 Статус дня для админского календаря

    Логика цветовой индикации:
    ✅ ❗️ ПРОШЕДШИЕ ДНИ  (< today)
    ✅ 📅 СЕГОДНЯ       (== today)
    ✅   МНОГО СВОБОДНЫХ (>5 слотов)
    ✅ 🟡 МАЛО СВОБОДНЫХ (1-5 слотов)
    ✅ ❗️ ПОЛНОСТЬЮ ЗАНЯТЫ (0 слотов)
    """
    today = date.today()

    # 🎯 1. ПРОШЕДШИЕ ДНИ = КРАСНЫЙ ❗️
    if day_date < today:
        return "❗️", "Прошедший день"

    # 🎯 2. СЕГОДНЯ = 📅
    if day_date == today:
        return "📅", "Сегодня"

    # 🎯 3. БУДУЩИЕ ДНИ по слотам
    slots = get_available_slots(day_date)
    free_count = len(slots)

    if free_count >= 6:  # >50% свободно (6 из 11)
        return "", f"Свободно: {free_count}"
    elif free_count >= 1:  # 1-5 слотов
        return "", f"Свободно: {free_count}" #🟡
    else:  # 0 слотов
        return "❗️", "Занято/выходной"


def get_admin_date_menu(date_str: str) -> InlineKeyboardMarkup:
    """
    📅 Меню управления конкретным днем (после выбора даты)

    Кнопки:
    ✅ 🛠 Слоты времени (⭕/✅ вкл/выкл)
    ✅ 🔙 Календарь / 🏠 Меню
    """
    markup = InlineKeyboardMarkup(row_width=2)

    markup.row(
        InlineKeyboardButton("🛠 Слоты времени", callback_data=f'admin_slots_{date_str}')
        # InlineKeyboardButton("📊 Статистика", callback_data=f'admin_stats_{date_str}')
    )
    markup.row(
        InlineKeyboardButton("🔙 Календарь", callback_data='admin_calendar'),
        InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')
    )

    return markup


def get_time_management_menu(date_str: str) -> InlineKeyboardMarkup:
    """🛠 Админ меню с блокировкой ДАТЫ + статусами времени"""
    markup = InlineKeyboardMarkup(row_width=4)
    day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    all_slots = WORK_HOURS

    # ✅ КНОПКА БЛОКИРОВКИ ВСЕЙ ДАТЫ (ПЕРВАЯ!)
    is_date_blocked = DateBlock.get_or_none(DateBlock.block_date == day_date)
    block_text = "🔓 Включить дату" if is_date_blocked else "🔒 Отключить дату"
    block_cb = f"toggle_date_{date_str}"

    markup.row(InlineKeyboardButton(block_text, callback_data=block_cb))

    # Время с ЭМОДЗИ статусами
    available_slots = get_available_slots(day_date)
    booked_slots = [b.time_slot for b in Booking.select().where(
        Booking.book_date == day_date, Booking.is_cancelled == False
    )]

    for i in range(0, len(all_slots), 4):
        row = all_slots[i:i + 4]
        row_buttons = []
        for slot in row:
            status_emoji = get_slot_status_emoji(slot, day_date, available_slots, booked_slots)
            row_buttons.append(
                InlineKeyboardButton(
                    f"{status_emoji} {slot}",
                    callback_data=f'toggle_slot_{date_str}_{slot}'
                )
            )
        markup.row(*row_buttons)

    markup.row(
        InlineKeyboardButton("⬅️ Календарь", callback_data=f"admin_date_{date_str}"),
        InlineKeyboardButton("🏠 Меню", callback_data="main_menu")
    )
    return markup


def get_slot_status_emoji(slot_time: str, book_date: date,
                          available_slots: List[str], booked_slots: List[str]) -> str:
    """🎨 Эмодзи статуса слота для админа"""
    # ❗️ Забронировано
    if slot_time in booked_slots:
        return "❗️"
    #  Доступно
    if slot_time in available_slots:
        return "" #🟢
    # ⭕ Отключено
    return "⭕"

