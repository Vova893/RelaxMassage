"""
Модели базы данных для Telegram-бота RelaxMassageBot.

Модели:
- User: пользователи Telegram
- UserActionLog: логи действий пользователей
- InlineButtonClick: логи нажатий inline-кнопок
- Booking: записи на массаж
- TimeSlot: управление доступностью слотов (админ)
- DateBlock: блокировка целых дат массажистом (админом)

Функции: создание таблиц, регистрация пользователей, логирование,
управление записями и слотами времени.
"""

from peewee import (
    Model, BigIntegerField, CharField, TextField,
    DateTimeField, DateField, BooleanField, ForeignKeyField, AutoField
)
from datetime import datetime, date
from typing import Optional, Union, List
from loader import database
from telebot.types import User as TgUser
from config_data.settings import WORK_HOURS


# Базовый класс для всех моделей
class BaseModel(Model):
    """Базовая модель со связанной БД"""

    class Meta:
        database = database


class User(BaseModel):
    """Модель пользователя Telegram"""
    telegram_id = BigIntegerField(primary_key=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)


class UserActionLog(BaseModel):
    """Лог действий пользователя"""
    user = ForeignKeyField(User, backref='actions', column_name='user_telegram_id')
    action_type = CharField()
    details = TextField(null=True)
    timestamp = DateTimeField(default=datetime.now)


class InlineButtonClick(BaseModel):
    """Логирование нажатий inline-кнопок"""
    user = ForeignKeyField(User, backref='clicks', column_name='user_telegram_id')
    button_label = CharField()
    input_value = TextField(null=True)
    timestamp = DateTimeField(default=datetime.now)


class Booking(BaseModel):
    """Записи на массаж"""
    DoesNotExist = None
    id = AutoField()
    user = ForeignKeyField(User, backref='bookings', column_name='user_telegram_id')
    user_name = CharField()
    phone = CharField(null=True)
    service = CharField()  # Пример: Классический массаж (60 мин)
    book_date = DateField()
    time_slot = CharField()  # Пример: 14:00
    created_at = DateTimeField(default=datetime.now)
    is_cancelled = BooleanField(default=False)


class TimeSlot(BaseModel):
    """Доступность слотов времени (для админов)"""
    book_date = DateField()
    time_slot = CharField()  # Пример: 09:00
    is_available = BooleanField(default=True)


class DateBlock(BaseModel):
    """🔒 Блокировка целых дат массажистом"""
    block_date = DateField(unique=True)
    reason = CharField(null=True, default="Выходной массажиста")

    class Meta:
        table_name = 'date_blocks'


def create_tables() -> None:
    """Создает все таблицы БД если они не существуют"""
    with database:
        database.create_tables([
            User, UserActionLog, InlineButtonClick,
            Booking, TimeSlot, DateBlock
        ])


def register_user_if_not_exists(tg_user: TgUser) -> User:
    """Регистрирует пользователя если его нет в БД"""
    with database.atomic():
        obj, created = User.get_or_create(
            telegram_id=tg_user.id,
            defaults={
                'username': tg_user.username,
                'first_name': tg_user.first_name,
                'last_name': tg_user.last_name
            }
        )
    return obj


def log_action(
    user: Union[User, int],
    action_type: str,
    details: Optional[str] = None
) -> None:
    """Логирует действие пользователя"""
    if isinstance(user, int):
        user_obj = User.get(telegram_id=user)
    else:
        user_obj = user

    with database.atomic():
        UserActionLog.create(
            user=user_obj,
            action_type=action_type,
            details=details
        )


def log_button_click(
    user: Union[User, int],
    button_label: str,
    input_value: Optional[str] = None
) -> None:
    """Логирует нажатие inline-кнопки"""
    if isinstance(user, int):
        user_obj = User.get(telegram_id=user)
    else:
        user_obj = user

    with database.atomic():
        InlineButtonClick.create(
            user=user_obj,
            button_label=button_label,
            input_value=input_value
        )


def get_user_bookings(telegram_id: int, limit: int = 5) -> List[Booking]:
    """Получить записи пользователя"""
    return list(Booking.select().where(
        Booking.user == User.get(telegram_id=telegram_id),
        Booking.is_cancelled == False
    ).order_by(Booking.created_at.desc()).limit(limit))


def get_all_bookings(limit: int = 10) -> List[Booking]:
    """Все активные записи (для админов)"""
    return list(Booking.select().where(
        Booking.is_cancelled == False
    ).order_by(Booking.created_at.desc()).limit(limit))

def get_slot_status_text(book_date: date) -> str:
    """
    📊 Текст статуса слотов для админа

    Args:
        book_date: дата для анализа

    Returns:
        "📅 20.02.2026\n🟢 Доступно: 8\n🔴 Отключено: 3"
    """
    from config_data.settings import WORK_HOURS
    available_slots: List[str] = get_available_slots(book_date)
    total_slots: int = len(WORK_HOURS)  # 11 слотов
    disabled_slots: int = total_slots - len(available_slots)

    return (
        f"📅 <b>{book_date.strftime('%Y-%m-%d')}</b>\n"
        f"🟢 Доступно: <b>{len(available_slots)}</b>\n"
        f"🔴 Отключено: <b>{disabled_slots}</b>"
    )


def get_detailed_slot_status(book_date: date) -> str:
    """Детальная статистика слотов с забронированными и отключенными временами"""

    all_slots = WORK_HOURS

    # ✅ ИСПРАВЛЕНО: available_slots это строки!
    available_slots = get_available_slots(book_date)  # ['09:00', '10:00']
    available_times = available_slots  # Уже строки!
    available_count = len(available_slots)

    # Забронированные слоты
    booked_slots = Booking.select(Booking.time_slot).where(
        Booking.book_date == book_date,
        Booking.is_cancelled == False
    )
    booked_count = booked_slots.count()
    booked_times = [slot.time_slot for slot in booked_slots]

    # ✅ ОТКЛЮЧЕННЫЕ: НЕ в available И НЕ забронированы
    disabled_times = []
    for slot_time in all_slots:
        if slot_time not in available_times and slot_time not in booked_times:
            disabled_times.append(slot_time)
    disabled_count = len(disabled_times)

    status_text = (
        f"📅 <b>{book_date.strftime('%Y-%m-%d')}</b>\n\n"
        f"🟢 Доступно: <b>{available_count}</b>\n"
        f"🔴 Забронировано: <b>{booked_count}</b>\n"
        f"⭕ Отключено: <b>{disabled_count}</b>\n\n"
    )

    # Список забронированных
    if booked_times:
        status_text += "🔴 <b>Забронировано:</b>\n"
        for time_slot in booked_times:
            status_text += f"• <b>{time_slot}</b>\n"

    return status_text


def get_available_slots(book_date: date) -> List[str]:
    """🟢 Доступные слоты с БЛОКИРОВКОЙ ДАТ + БРОНИ + ОТКЛЮЧЕНИЯ"""
    # 🔒 Если дата заблокирована полностью - НИЧЕГО доступно
    if DateBlock.get_or_none(DateBlock.block_date == book_date):
        return []

    all_slots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
                 '15:00', '16:00', '17:00', '18:00', '19:00']

    # ❌ Занятые записи пользователей
    booked_slots = Booking.select(Booking.time_slot).where(  # ✅ timeslot!
        Booking.book_date == book_date,
        Booking.is_cancelled == False
    )

    # ❌ Отключенные админом слоты
    admin_disabled = TimeSlot.select(TimeSlot.time_slot).where(
        TimeSlot.book_date == book_date,
        TimeSlot.is_available == False
    )

    unavailable = {b.time_slot for b in booked_slots} | {t.time_slot for t in admin_disabled}  # ✅ timeslot!

    return [slot for slot in all_slots if slot not in unavailable]


def cancel_booking(booking_id: int) -> bool:
    """Отменить запись по ID"""
    try:
        booking = Booking.get(Booking.id == booking_id)
        booking.is_cancelled = True
        booking.save()
        return True
    except Booking.DoesNotExist:
        return False


def is_admin(telegram_id: int) -> bool:
    """Проверка прав администратора"""
    from config_data.config import ADMIN_ID
    return telegram_id in ADMIN_ID


def set_time_slot_availability(
    book_date: date,
    time_slot: str,
    available: bool
) -> bool:
    """Админ: установить доступность слота времени"""
    with database.atomic():
        # Удаляем старые записи для этой даты/времени
        TimeSlot.delete().where(
            TimeSlot.book_date == book_date,
            TimeSlot.time_slot == time_slot
        ).execute()

        # Создаем новую запись
        TimeSlot.create(
            book_date=book_date,
            time_slot=time_slot,
            is_available=available
        )
    return True


# ✅ Экспорт ВСЕХ функций для импортов
__all__ = [
    'create_tables',
    'register_user_if_not_exists',
    'is_admin',
    'get_available_slots',
    'set_time_slot_availability',
    'get_user_bookings',
    'get_all_bookings',
    'get_slot_status_text',
    'log_button_click',
    'User', 'TimeSlot', 'Booking'
]
