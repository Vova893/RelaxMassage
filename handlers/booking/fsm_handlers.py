"""
✅ FSM обработчики - ЧИСТЫЕ и РАБОЧИЕ
"""

from __future__ import annotations
from telebot.types import Message, CallbackQuery
from loader import bot
from datetime import datetime, date, timedelta
from database.database import (
    register_user_if_not_exists, Booking, get_available_slots, log_action
)
from keyboards.reply.reply_button import get_main_menu
from keyboards.inline.date_menu import get_time_menu, get_phone_keyboard
from states.states import UserStates
from utils.booking_notificatin import booking_notification

# ГЛОБАЛЬНАЯ БЛОКИРОВКА
processing_lock = {}


def process_name(message):
    """Обработка имени пользователя"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # ✅ Очистка старых handlers
    try:
        bot.clear_step_handler_by_chat_id(chat_id)
    except:
        pass

    # ✅ Блокировка дублирования
    if chat_id in processing_lock:
        # print(f"⏳ process_name: Уже обрабатывается {chat_id}")
        return

    processing_lock[chat_id] = True
    # print(f"✅ Имя получено: {message.text}")

    try:
        user = register_user_if_not_exists(message.from_user)

        # ✅ КРИТИЧНО: сохраняем username в FSM
        with bot.retrieve_data(user.telegram_id, chat_id) as data:
            data['user_name'] = message.text

        # Запрашиваем телефон
        bot.send_message(
            chat_id,
            f"✅ <b>Имя:</b> {message.text}\n\n👇<b>Нажмите на кнопку '📞 Ввести телефон'\n"
            f"а затем введите номер телефона:</b>",
            reply_markup=get_phone_keyboard(),
            parse_mode="HTML"
        )

        # Регистрируем следующий шаг
        bot.register_next_step_handler_by_chat_id(chat_id, process_phone)

    except Exception as e:
        print(f"❌ process_name error: {e}")
        bot.send_message(chat_id, "❌ Ошибка. Попробуйте снова.")

    finally:
        # Освобождаем блокировку
        if chat_id in processing_lock:
            del processing_lock[chat_id]


def process_phone(message):
    """Создание бронирования из телефона"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # ✅ Очистка старых handlers
    try:
        bot.clear_step_handler_by_chat_id(chat_id)
    except:
        pass

    # ✅ 1. ПРОВЕРКА user_name ПЕРЕД блокировкой
    user = register_user_if_not_exists(message.from_user)
    with bot.retrieve_data(user.telegram_id, chat_id) as data:
        user_name = data.get('user_name')
        if not user_name:
            bot.send_message(chat_id, "❌ Имя не найдено! Начните заново.")
            bot.delete_state(user_id, chat_id)
            bot.send_message(chat_id, "🏠 Главное меню:", reply_markup=get_main_menu(user_id))
            return

    # ✅ 2. Блокировка только если user_name есть
    if chat_id in processing_lock:
        # print(f"⏳ process_phone: Уже обрабатывается {chat_id}")
        return

    processing_lock[chat_id] = True
    # print("🎯 Создаем запись...")

    try:
        # Читаем все данные FSM
        with bot.retrieve_data(user.telegram_id, chat_id) as data:
            user_name = data.get('user_name')
            service = data.get('service') or data.get('selected_service')
            selected_date = data.get('selected_date')
            selected_time = data.get('selected_time')
            phone = message.text

        # print(f"🔍 Данные: username='{user_name}', service='{service}', phone='{phone}'")

        # Проверяем ВСЕ обязательные поля
        if not all([user_name, service, selected_date, selected_time]):
            missing = []
            if not user_name: missing.append('имя')
            if not service: missing.append('услуга')
            if not selected_date: missing.append('дата')
            if not selected_time: missing.append('время')

            bot.send_message(chat_id, f"❌ Не хватает: {', '.join(missing)}")
            return

        # ✅ Создаем бронь
        booking = Booking.create(
            user=user,
            user_name=user_name,
            phone=phone,
            service=service,
            book_date=datetime.strptime(selected_date, '%Y-%m-%d').date(),
            time_slot=selected_time
        )

        # Подтверждение
        confirmation = (
            f"✅ <b>Бронь №{booking.id} создана!</b>\n\n"
            f"📅 <b>{selected_date}</b>\n"
            f"🕐 <b>{selected_time}</b>\n"
            f"💆 <b>{service}</b>\n"
            f"👤 <b>{user_name}</b>\n"
            f"📱 <code>{phone}</code>"
        )
        bot.send_message(chat_id, confirmation, parse_mode='HTML')
        booking_notification(booking)

    except Exception as e:
        print(f"❌ Ошибка создания брони: {e}")
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")

    finally:
        # ✅ Полная очистка
        if chat_id in processing_lock:
            del processing_lock[chat_id]
        bot.delete_state(user_id, chat_id)
        bot.send_message(chat_id, "🏠 Главное меню:",
                         reply_markup=get_main_menu(user_id))


@bot.message_handler(state=UserStates.waiting_date_custom)
def process_custom_date(message: Message) -> None:
    """📅 Кастомная дата"""
    try:
        book_date = datetime.strptime(message.text, '%Y-%m-%d').date()
        max_date = date.today() + timedelta(days=30)

        if book_date < date.today() or book_date > max_date:
            bot.send_message(message.chat.id, f"❌ Дата: сегодня - {max_date.strftime('%Y-%m-%d')}")
            return

        slots = get_available_slots(book_date)
        if slots:
            bot.send_message(
                message.chat.id,
                "🕐 Выберите время:",
                reply_markup=get_time_menu(str(book_date), slots)
            )
        else:
            bot.send_message(message.chat.id, "❌ Нет свободных слотов")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Формат: ДД.ММ.ГГГГ")

    bot.delete_state(message.from_user.id, message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == 'enter_your_full_name'
                                              or call.data == 'enter_a_phone'
                                              or call.data == 'cancellation')
def handle_name_phone_buttons(call: CallbackQuery) -> None:
    """👤📞 Inline кнопки → состояние ожидания текста"""
    # Обязательный ответ на callback_query!
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    user = register_user_if_not_exists(
        call.from_user)  # Проверяется существование пользователя, если его нет то регистрируется
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "enter_your_full_name":
        bot.edit_message_text(
            "✍️ <b>Введите ФИО:</b>\n\nИванов Иван Иванович",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        log_action(user, '👤 Ввести ФИО', details='Нажата кнопка "Ввести ФИО"')
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_name)

    if call.data == "enter_a_phone":
        bot.edit_message_text(
            "📞 <b>Введите телефон:</b>\n\n+7(999)123-45-67",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        log_action(user, '📞 Ввести телефон', details='Нажата кнопка "Ввести телефон"')
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_phone)

    if call.data == "cancellation":
        bot.delete_state(user_id, chat_id)
        bot.send_message(chat_id, "❌ Отменено", reply_markup=get_main_menu(user_id))
