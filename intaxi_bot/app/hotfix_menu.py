from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.miniapp_routes import city_main_url, intercity_main_url
from app.strings import MESSAGES


def home_webapp_menu(lang: str, *, is_driver_mode: bool = False) -> ReplyKeyboardMarkup:
    m = MESSAGES.get(lang, MESSAGES['ru'])
    city_text = m.get('btn_fast_order', '⚡ Fast order')
    intercity_text = m.get('btn_intercity_driver' if is_driver_mode else 'btn_intercity_passenger', m.get('btn_intercity', '🛣 Intercity'))
    profile_text = m.get('btn_profile', '👤 Profile')
    wallet_text = m.get('btn_wallet', '💰 Wallet')
    feedback_text = m.get('btn_feedback', '💬 Feedback')
    current_order_text = m.get('btn_current_order', '📌 Текущий заказ')

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
