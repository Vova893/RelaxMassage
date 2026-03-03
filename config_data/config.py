"""
Конфигурация Telegram-бота RelaxMassageBot.

Загружает переменные окружения из .env:
- BOT_TOKEN: токен бота от @BotFather
- ADMIN_ID: список ID администраторов (через запятую)
- DB_PATH: путь к базе данных SQLite

Экспорт: BOT_TOKEN, ADMIN_ID, DB_PATH, DEFAULT_COMMANDS
"""

import os
from dotenv import find_dotenv, load_dotenv
from typing import Tuple, List


if not find_dotenv():
    raise SystemExit('❌ Переменные окружения не загружены, т.к. отсутствует файл .env')

load_dotenv()

# Токен бота от @BotFather
BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')

# Список ID администраторов (через запятую в .env)
ADMIN_ID: List[int] = [
    int(id.strip()) for id in os.getenv('ADMIN_ID', '').split(',') if id.strip()
]

# Путь к базе данных
DB_PATH: str = os.getenv('DB_PATH', 'massage_bookings.db')

# Команды меню бота
DEFAULT_COMMANDS: Tuple[Tuple[str, str], ...] = (
    ('start', '🏠 Главное меню'),
    ('help', 'Справка'),
)