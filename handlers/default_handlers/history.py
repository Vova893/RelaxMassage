from telebot import types
from loader import bot
from peewee import DoesNotExist
from database.database import (
    Booking, register_user_if_not_exists,
    get_user_bookings, log_action, is_admin
)
from config_data.config import ADMIN_ID


@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def handle_cancel_booking(call: types.CallbackQuery):
    """Обработка отмены бронирования"""
    try:
        # Извлекаем ID брони
        booking_id = int(call.data.split('_')[1])
        user = register_user_if_not_exists(call.from_user)

        # Находим бронь
        booking = Booking.get_or_none(Booking.id == booking_id)
        if not booking:
            bot.answer_callback_query(call.id, "❌ Бронь не найдена!", show_alert=True)
            return

        # Проверка прав доступа
        if booking.user.telegram_id != user.telegram_id and not is_admin(user.telegram_id):
            bot.answer_callback_query(call.id, "❌ Нет прав для отмены!", show_alert=True)
            return

        # Проверка статуса
        if booking.is_cancelled:
            bot.answer_callback_query(call.id, "ℹ️ Бронь уже отменена!", show_alert=True)
            return

        # ✅ ОТМЕНЯЕМ БРОНЬ
        booking.is_cancelled = True
        booking.save()

        # Обновляем сообщение
        text = (
            f"✅ <b>Бронь #{booking_id} отменена!</b>\n\n"
            f"📅 <b>{booking.book_date}</b>\n"
            f"🕐 <b>{booking.time_slot}</b>\n"
            f"💆 <b>{booking.service}</b>\n"
            f"👤 <b>{booking.user_name}</b>"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        try:
            for admin_id in ADMIN_ID:
                bot.send_message(admin_id, text, parse_mode='HTML')

        except Exception as e:
            print(f'Ошибка уведомления админа: {e}')

        # Логируем
        log_action(user.telegram_id, "cancel_booking", f"Бронь #{booking_id}")
        bot.answer_callback_query(call.id, "✅ Отменено!")

    except ValueError:
        bot.answer_callback_query(call.id, "❌ Неверный формат!", show_alert=True)
    except DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Бронь не найдена!", show_alert=True)
    except Exception as e:
        print(f"❌ Cancel error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == 'history_all')
def handle_history_all(call: types.CallbackQuery):
    """Показать все брони пользователя (активные + отмененные)"""
    try:
        user_id = call.from_user.id
        # Получаем ВСЕ брони (limit=None)
        all_bookings = get_user_bookings(user_id, limit=20)

        text = "📜 <b>Все ваши брони:</b>\n\n"
        if not all_bookings:
            text += "📝 Пока нет броней"
        else:
            for booking in all_bookings:
                status = "❌ Отменена" if booking.is_cancelled else "✅ Активна"
                text += (
                    f"<b>#{booking.id}</b> {status}\n"
                    f"🗓️ {booking.book_date} {booking.time_slot}\n"
                    f"💆 {booking.service}\n"
                    f"👤 {booking.user_name}\n\n"
                )

        # Клавиатура только с главным меню (нельзя отменять отмененные)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"❌ History all error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка загрузки!", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == 'history_active')
def handle_history_active(call: types.CallbackQuery):
    """Вернуться к активным броням"""
    try:
        from database.database import get_user_bookings
        active_bookings = [
            b for b in get_user_bookings(call.from_user.id)
            if not b.is_cancelled
        ]

        from keyboards.inline.date_menu import get_history_menu
        markup = get_history_menu(active_bookings)

        # Пересоздаем сообщение с активными бронями
        text = "📋 <b>Ваши активные записи:</b>\n\n"
        for booking in active_bookings:
            text += (
                f"🗓️ {booking.book_date} {booking.time_slot}\n"
                f"💆 {booking.service}\n"
                f"👤 {booking.user_name}\n\n"
            )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"❌ History active error: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка!", show_alert=True)
