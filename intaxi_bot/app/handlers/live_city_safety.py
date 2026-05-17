from __future__ import annotations

from typing import Any

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

import app.order_actions as order_actions
from app.database.models import CityOrderV1, CityTripV1, DriverOnlineState, User, Vehicle, async_session
from app.handlers.live_city import CityCreateFlow, _send_trip_cards, _text, _user_lang

router = Router()

LIVE_CITY_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}


def _clean(value: Any) -> str:
    return str(value or '').strip().lower()


def _same_or_empty(left: Any, right: Any) -> bool:
    left_value = _clean(left)
    right_value = _clean(right)
    return not left_value or not right_value or left_value == right_value


def _price_to_minor_units(price: float) -> int:
    return int(round(float(price) * 100))


def _minor_units_to_price(value: str) -> float:
    return round(int(value) / 100, 2)


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _can_driver_use_order(session, *, order_id: int, driver_tg_id: int) -> tuple[bool, str]:
    lang = await _user_lang(session, driver_tg_id)
    order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
    driver = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
    if not order or not driver or order.status != 'active' or order.role != 'passenger' or order.creator_tg_id == driver_tg_id:
        return False, lang
    if not driver.is_verified or _clean(driver.active_role) != 'driver':
        return False, lang
    vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == driver.id))
    if not vehicle:
        return False, lang
    state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver_tg_id))
    if not state or not state.is_online:
        return False, lang
    if not _same_or_empty(state.country, order.country) or not _same_or_empty(state.city, order.city):
        return False, lang
    if await _driver_has_live_trip(session, driver_tg_id):
        return False, lang
    return True, lang


@router.callback_query(F.data.startswith('lccacc_'))
async def safe_driver_accept(callback: types.CallbackQuery, bot: Bot):
    order_id = int((callback.data or '').split('_')[-1])
    async with async_session() as session:
        lang = await _user_lang(session, callback.from_user.id)
    trip = await order_actions.accept_city_offer_for_user(order_id, callback.from_user.id)
    if not trip:
        await callback.answer(_text(lang, 'accept_failed'), show_alert=True)
        return
    await callback.answer(_text(lang, 'accepted'))
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lccoffer_'))
async def safe_driver_offer_price(callback: types.CallbackQuery, state: FSMContext):
    order_id = int((callback.data or '').split('_')[-1])
    async with async_session() as session:
        allowed, lang = await _can_driver_use_order(session, order_id=order_id, driver_tg_id=callback.from_user.id)
    if not allowed:
        await callback.answer(_text(lang, 'accept_failed'), show_alert=True)
        return
    await state.set_state(CityCreateFlow.offer_price)
    await state.update_data(order_id=order_id, driver_tg_id=callback.from_user.id, lang=lang)
    await callback.message.answer(_text(lang, 'offer_price_prompt'))
    await callback.answer()


@router.message(CityCreateFlow.offer_price)
async def safe_driver_offer_price_submit(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer(_text(lang, 'price_retry'))
        return
    if price <= 0:
        await message.answer(_text(lang, 'price_retry'))
        return
    order_id = int(data.get('order_id'))
    driver_tg_id = int(data.get('driver_tg_id'))
    if message.from_user.id != driver_tg_id:
        await state.clear()
        await message.answer(_text(lang, 'order_unavailable'))
        return
    async with async_session() as session:
        allowed, lang = await _can_driver_use_order(session, order_id=order_id, driver_tg_id=driver_tg_id)
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id)) if allowed else None
        passenger_lang = await _user_lang(session, order.creator_tg_id) if order else lang
    if not allowed or not order:
        await state.clear()
        await message.answer(_text(lang, 'order_unavailable'))
        return
    price_minor = _price_to_minor_units(price)
    builder = InlineKeyboardBuilder()
    builder.button(text=_text(passenger_lang, 'accept_price'), callback_data=f'lcpacc_{order_id}_{driver_tg_id}_{price_minor}')
    builder.button(text=_text(passenger_lang, 'reject'), callback_data=f'lcprej_{order_id}_{driver_tg_id}')
    builder.adjust(1)
    try:
        await bot.send_message(order.creator_tg_id, f"{_text(passenger_lang, 'driver_offered_price')}: {price:g}", reply_markup=builder.as_markup())
    except Exception:
        pass
    await state.clear()
    await message.answer(_text(lang, 'offer_sent'))


@router.callback_query(F.data.startswith('lcpacc_'))
async def safe_passenger_accept_price(callback: types.CallbackQuery, bot: Bot):
    parts = (callback.data or '').split('_')
    if len(parts) != 4:
        await callback.answer(show_alert=True)
        return
    _, order_id_raw, driver_tg_id_raw, price_raw = parts
    order_id = int(order_id_raw)
    driver_tg_id = int(driver_tg_id_raw)
    price = _minor_units_to_price(price_raw)
    async with async_session() as session:
        lang = await _user_lang(session, callback.from_user.id)
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id).with_for_update())
        if not order or order.creator_tg_id != callback.from_user.id or order.status != 'active' or order.role != 'passenger':
            await callback.answer(_text(lang, 'offer_accept_failed'), show_alert=True)
            return
        order.price = price
        await session.commit()
    trip = await order_actions.accept_city_offer_for_user(order_id, driver_tg_id)
    if not trip:
        await callback.answer(_text(lang, 'offer_accept_failed'), show_alert=True)
        return
    await callback.answer(_text(lang, 'price_accepted'))
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lcprej_'))
async def safe_passenger_reject_price(callback: types.CallbackQuery, bot: Bot):
    parts = (callback.data or '').split('_')
    if len(parts) != 3:
        await callback.answer(show_alert=True)
        return
    _, order_id_raw, driver_tg_id_raw = parts
    order_id = int(order_id_raw)
    driver_tg_id = int(driver_tg_id_raw)
    async with async_session() as session:
        passenger_lang = await _user_lang(session, callback.from_user.id)
        driver_lang = await _user_lang(session, driver_tg_id)
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        if not order or order.creator_tg_id != callback.from_user.id or order.status != 'active' or order.role != 'passenger':
            await callback.answer(_text(passenger_lang, 'order_unavailable'), show_alert=True)
            return
    try:
        await bot.send_message(driver_tg_id, f"{_text(driver_lang, 'price_rejected_driver')} #{order_id}.")
    except Exception:
        pass
    await callback.answer(_text(passenger_lang, 'offer_rejected'))
