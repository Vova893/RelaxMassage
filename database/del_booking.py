import schedule
import pytz
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from database.database import Booking, database



# Moscow timezone (UTC+3)
moscow_tz = pytz.timezone('Europe/Moscow')


def cleanup_old_bookings() -> int:
    """🗑 Удаляет записи старше 1 месяца"""
    try:
        database.connect()  # ✅ Подключение БД

        cutoff_date = date.today() - relativedelta(months=1)
        deleted = Booking.delete().where(
            Booking.book_date < cutoff_date,
            Booking.is_cancelled == False
        ).execute()

        # print(f"🗑 [{datetime.now(moscow_tz)}] Удалено {deleted} записей (до {cutoff_date})")
        return deleted

    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        return 0
    finally:
        database.close()  # ✅ Закрытие БД



schedule.every().day.at("03:00").do(cleanup_old_bookings)


def run_scheduler():
    """Фоновый планировщик"""
    while True:
        schedule.run_pending()
        time.sleep(60)