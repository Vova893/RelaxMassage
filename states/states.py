"""
FSM-состояния для RelaxMassageBot.

Состояния для пошаговой записи:
- waiting_date_custom: ввод кастомной даты
- waiting_time: выбор времени
- waiting_service: выбор услуги
- waiting_name_phone: ввод ФИО+телефон
- waiting_name: ФИО пользователя при бронировании
- waiting_phone: номер телефона пользователя при бронировании
"""

from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

storage = StateMemoryStorage()


class UserStates(StatesGroup):
    """Состояния FSM пользователя"""
    waiting_date_custom = State()
    waiting_time = State()
    waiting_service = State()
    waiting_name_phone = State()
    waiting_name = State()
    waiting_phone = State()
