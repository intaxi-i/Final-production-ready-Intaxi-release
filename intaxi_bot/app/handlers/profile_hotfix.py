from __future__ import annotations

from aiogram import Router, types
from sqlalchemy import select

import app.database.requests as rq
from app.database.models import Vehicle, async_session
from app.strings import MESSAGES

router = Router()

BUTTONS = {
    "ru": {"settings": "⚙️ Изменить данные", "wallet": "💰 Баланс", "feedback": "💬 Отзывы и предложения", "back": "⬅️ Назад"},
    "uz": {"settings": "⚙️ Ma’lumotlarni o‘zgartirish", "wallet": "💰 Balans", "feedback": "💬 Fikr va takliflar", "back": "⬅️ Orqaga"},
    "en": {"settings": "⚙️ Edit data", "wallet": "💰 Wallet", "feedback": "💬 Reviews and suggestions", "back": "⬅️ Back"},
    "ar": {"settings": "⚙️ تعديل البيانات", "wallet": "💰 الرصيد", "feedback": "💬 الآراء والاقتراحات", "back": "⬅️ رجوع"},
}


def _lang(user) -> str:
    value = (getattr(user, 'language', None) or 'ru').lower()
    return value if value in BUTTONS else 'ru'


def _text(lang: str, key: str) -> str:
    return BUTTONS.get(lang, BUTTONS['ru'])[key]


def _profile_kb(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=_text(lang, 'wallet'))],
            [types.KeyboardButton(text=_text(lang, 'settings'))],
            [types.KeyboardButton(text=_text(lang, 'feedback'))],
            [types.KeyboardButton(text=_text(lang, 'back'))],
        ],
        resize_keyboard=True,
    )


async def _build_profile_text(user) -> str:
    lang = _lang(user)
    currency = MESSAGES.get(lang, MESSAGES['ru']).get('currencies', {}).get(user.country, 'USD')
    async with async_session() as session:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
    lines = [
        f"<b>{user.full_name or '—'}</b>",
        f"ID: <code>{user.tg_id}</code>",
        f"Username: @{user.username or '—'}",
        f"{user.country or '—'}, {user.city or '—'}",
        f"Баланс: {user.balance or 0} {currency}",
        "Комиссия: 0%",
    ]
    if user.is_verified and (user.active_role or 'driver') != 'passenger' and vehicle:
        lines.extend([
            "",
            "🚖 <b>Водитель</b>",
            f"Авто: {vehicle.brand or ''} {vehicle.model or ''}",
            f"Номер: {vehicle.plate or '—'}",
            f"Цвет: {vehicle.color or '—'}",
            f"Вместимость: {vehicle.capacity or '—'}",
        ])
    return '\n'.join(lines)


@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_profile') for l in MESSAGES))
async def show_profile_hotfix(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = _lang(user)
    await message.answer(await _build_profile_text(user), reply_markup=_profile_kb(lang), parse_mode='HTML')
