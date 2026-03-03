"""
🚀 RelaxMassageBot v1.0 - Массажный салон бота

Полная документация:
✅ Бронирование массажа (календарь + слоты)
✅ Админ панель (управление слотами/выходными)
✅ FSM состояния (безопасная запись)
✅ Модульная архитектура (50+ файлов)
✅ Peewee ORM (SQLite)
✅ Type hints (IDE friendly)

Запуск: python main.py
"""

import logging
import threading
from loader import bot
from handlers import *  # 🎯 Авторегистрация обработчиков
from database.database import create_tables
from database.del_booking import run_scheduler

# ✅ Логирование (файл + консоль)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),  # 📄 Файл логов
        logging.StreamHandler()  # 📌 Консольный вывод
    ]
)
logger = logging.getLogger(__name__)  # 🔗 Основной логгер приложения


def main() -> None:
    """🎯 Главная функция запуска"""

    # ✅ Инициализация БД
    create_tables()

    print("=" * 60)
    print("🤖 RelaxMassageBot v1.0 успешно запущен!")
    print("=" * 60)

    # Запуск планировщика в фоне
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # 🚀 Запуск
    try:
        bot.infinity_polling(
            none_stop=True,  # Продолжаем опрос сервера даже при ошибках
            interval=1,  # Интервал опроса серверов Телеграма
            timeout=30,  # Таймаут ожидания ответа от API
            logger_level=logging.INFO
        )
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)


if __name__ == '__main__':
    main()
