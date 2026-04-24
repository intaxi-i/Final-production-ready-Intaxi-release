from __future__ import annotations

import json
from pathlib import Path

from aiogram import F, Router, types
from sqlalchemy import select

import app.database.requests as rq
from app.database.models import Vehicle, async_session
from app.strings import MESSAGES

router = Router()

_SUPPORT_OPEN: set[int] = set()
_QURAN_ENABLED: set[int] = set()

BUTTONS = {
    "ru": {"support": "🤝 Поддержать наш проект", "quran": "Qur'on eslatma", "settings": "⚙️ Изменить данные", "wallet": "💰 Баланс", "feedback": "💬 Отзывы и предложения", "back": "⬅️ Назад", "hide": "Скрыто", "shown": "Показано", "on": "Включено", "off": "Выключено"},
    "uz": {"support": "🤝 Loyihamizni qo‘llab-quvvatlash", "quran": "Qur'on eslatma", "settings": "⚙️ Ma’lumotlarni o‘zgartirish", "wallet": "💰 Balans", "feedback": "💬 Fikr va takliflar", "back": "⬅️ Orqaga", "hide": "Yashirilgan", "shown": "Ko‘rsatilgan", "on": "Yoqilgan", "off": "O‘chirilgan"},
    "en": {"support": "🤝 Support our project", "quran": "Qur'on eslatma", "settings": "⚙️ Edit data", "wallet": "💰 Wallet", "feedback": "💬 Reviews and suggestions", "back": "⬅️ Back", "hide": "Hidden", "shown": "Shown", "on": "Enabled", "off": "Disabled"},
    "ar": {"support": "🤝 ادعم مشروعنا", "quran": "Qur'on eslatma", "settings": "⚙️ تعديل البيانات", "wallet": "💰 الرصيد", "feedback": "💬 الآراء والاقتراحات", "back": "⬅️ رجوع", "hide": "مخفي", "shown": "معروض", "on": "مفعل", "off": "متوقف"},
}


def _lang(user) -> str:
    value = (getattr(user, 'language', None) or 'ru').lower()
    return value if value in BUTTONS else 'ru'


def _text(lang: str, key: str) -> str:
    return BUTTONS.get(lang, BUTTONS['ru'])[key]


def _support_file_candidates() -> list[Path]:
    root = Path(__file__).resolve()
    return [
        root.parents[3] / 'shared' / 'support-data.json',
        root.parents[2] / 'shared' / 'support-data.json',
        Path('/opt/intaxi/shared/support-data.json'),
        Path('/opt/intaxi/repo/shared/support-data.json'),
    ]


def _load_support_data() -> dict:
    for path in _support_file_candidates():
        try:
            if path.exists():
                return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
    return {"fiat": [], "crypto": []}


def _profile_kb(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=_text(lang, 'wallet'))],
            [types.KeyboardButton(text=_text(lang, 'settings'))],
            [types.KeyboardButton(text=_text(lang, 'support'))],
            [types.KeyboardButton(text=_text(lang, 'quran'))],
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
    if user.tg_id in _SUPPORT_OPEN:
        support = _load_support_data()
        fiat = [item for item in support.get('fiat', []) if item.get('value')]
        crypto = [item for item in support.get('crypto', []) if item.get('value')]
        lines.extend(["", f"🤝 <b>{_text(lang, 'support')}</b>"])
        for item in fiat + crypto:
            lines.append(f"{item.get('label', '—')}: <code>{item.get('value', '')}</code>")
    else:
        lines.extend(["", f"🤝 {_text(lang, 'support')}: {_text(lang, 'hide')}"])
    lines.append(f"☪️ {_text(lang, 'quran')}: {_text(lang, 'on') if user.tg_id in _QURAN_ENABLED else _text(lang, 'off')}")
    return '\n'.join(lines)


@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_profile') for l in MESSAGES))
async def show_profile_hotfix(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = _lang(user)
    await message.answer(await _build_profile_text(user), reply_markup=_profile_kb(lang), parse_mode='HTML')


@router.message(lambda message: any(message.text == BUTTONS[l]['support'] for l in BUTTONS))
async def toggle_support_hotfix(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    if user.tg_id in _SUPPORT_OPEN:
        _SUPPORT_OPEN.discard(user.tg_id)
    else:
        _SUPPORT_OPEN.add(user.tg_id)
    lang = _lang(user)
    await message.answer(await _build_profile_text(user), reply_markup=_profile_kb(lang), parse_mode='HTML')


@router.message(lambda message: any(message.text == BUTTONS[l]['quran'] for l in BUTTONS))
async def toggle_quran_hotfix(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    if user.tg_id in _QURAN_ENABLED:
        _QURAN_ENABLED.discard(user.tg_id)
    else:
        _QURAN_ENABLED.add(user.tg_id)
    lang = _lang(user)
    await message.answer(await _build_profile_text(user), reply_markup=_profile_kb(lang), parse_mode='HTML')
