"""
Модуль инициализации бота с FSM-хранилищем для RelaxMassageBot.

Инициализация:
1. SQLite база данных ('massage_bookings.db')
2. TeleBot с StateMemoryStorage для FSM
3. Логирование INFO уровня
4. Переменная bots_abilities для приветствия

Экспорт: bot, bots_abilities, database
"""

import logging
from telebot import TeleBot
from peewee import SqliteDatabase
from config_data.config import BOT_TOKEN, DB_PATH
from states.states import storage  # FSM хранилище состояний

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Инициализация базы данных SQLite
database: SqliteDatabase = SqliteDatabase(DB_PATH)

# Создание бота с FSM хранилищем (ПЕРЕД импортом handlers!)
bot: TeleBot = TeleBot(
    token=BOT_TOKEN,
    state_storage=storage,  # Поддержка состояний FSM
    parse_mode='HTML'  # HTML разметка по умолчанию
)

# Текст возможностей бота (используется в /start)
bots_abilities: str = """
🤖 Бот для записи на массаж.

📅 Выберите удобную дату и время
💆 Выберите услугу из прайса
📱 Подтвердите запись с контактными данными
"""

# Экспорт объектов модуля
__all__ = ['bot', 'bots_abilities', 'database']
