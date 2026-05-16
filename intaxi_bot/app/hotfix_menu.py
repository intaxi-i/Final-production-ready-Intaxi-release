from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.miniapp_routes import city_main_url, intercity_main_url
from app.strings import MESSAGES

FALLBACK_LABELS = {
    'ru': {
        'btn_fast_order': '⚡ Быстрый заказ',
        'btn_intercity': '🛣 Межгород',
        'btn_profile': '👤 Профиль',
        'btn_wallet': '💰 Баланс',
        'btn_feedback': '💬 Отзывы и предложения',
        'btn_current_order': '📌 Текущий заказ',
    },
    'uz': {
        'btn_fast_order': '⚡ Tez buyurtma',
        'btn_intercity': '🛣 Shaharlararo',
        'btn_profile': '👤 Profil',
        'btn_wallet': '💰 Balans',
        'btn_feedback': '💬 Fikr va takliflar',
        'btn_current_order': '📌 Joriy buyurtma',
    },
    'en': {
        'btn_fast_order': '⚡ Fast order',
        'btn_intercity': '🛣 Intercity',
        'btn_profile': '👤 Profile',
        'btn_wallet': '💰 Wallet',
        'btn_feedback': '💬 Feedback and suggestions',
        'btn_current_order': '📌 Current order',
    },
    'ar': {
        'btn_fast_order': '⚡ طلب سريع',
        'btn_intercity': '🛣 بين المدن',
        'btn_profile': '👤 الملف الشخصي',
        'btn_wallet': '💰 الرصيد',
        'btn_feedback': '💬 الملاحظات والاقتراحات',
        'btn_current_order': '📌 الطلب الحالي',
    },
}


def _label(lang: str, key: str) -> str:
    code = lang if lang in FALLBACK_LABELS else 'ru'
    return MESSAGES.get(code, MESSAGES['ru']).get(key) or FALLBACK_LABELS[code].get(key) or FALLBACK_LABELS['ru'].get(key) or key


def home_webapp_menu(lang: str, *, is_driver_mode: bool = False) -> ReplyKeyboardMarkup:
    code = lang if lang in FALLBACK_LABELS else 'ru'
    m = MESSAGES.get(code, MESSAGES['ru'])
    city_text = _label(code, 'btn_fast_order')
    intercity_text = m.get('btn_intercity_driver' if is_driver_mode else 'btn_intercity_passenger') or _label(code, 'btn_intercity')
    profile_text = _label(code, 'btn_profile')
    wallet_text = _label(code, 'btn_wallet')
    feedback_text = _label(code, 'btn_feedback')
    current_order_text = _label(code, 'btn_current_order')

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=city_text, web_app=types.WebAppInfo(url=city_main_url('driver' if is_driver_mode else 'passenger'))),
                KeyboardButton(text=intercity_text, web_app=types.WebAppInfo(url=intercity_main_url('driver' if is_driver_mode else 'passenger'))),
            ],
            [KeyboardButton(text=current_order_text)],
            [KeyboardButton(text=profile_text), KeyboardButton(text=wallet_text)],
            [KeyboardButton(text=feedback_text)],
        ],
        resize_keyboard=True,
    )
