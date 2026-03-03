"""
✅ Авторегистрация ВСЕХ обработчиков RelaxMassageBot
Порядок КРИТИЧЕН!
"""

from . import booking
from . import default_handlers
# from .booking.main_handler import *           # 1️⃣ Главный callback_query
# from .booking.fsm_handlers import *           # 2️⃣ FSM состояния
# from .default_handlers.start import *         # 3️⃣ /start + reply-кнопки
# from .default_handlers.help import *          # 4️⃣ /help
# from .default_handlers.echo import *          # 5️⃣ ❌ Неизвестное ПОСЛЕДНИМ!
