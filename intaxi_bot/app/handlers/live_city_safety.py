from __future__ import annotations

from aiogram import Bot, F, Router, types
from sqlalchemy import select

import app.order_actions as order_actions
from app.database.models import CityOrderV1, async_session
from app.handlers.live_city import _send_trip_cards, _text, _user_lang

router = Router()


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


@router.callback_query(F.data.startswith('lcpacc_'))
async def safe_passenger_accept_price(callback: types.CallbackQuery, bot: Bot):
    parts = (callback.data or '').split('_')
    if len(parts) != 4:
        await callback.answer(show_alert=True)
        return
    _, order_id_raw, driver_tg_id_raw, price_raw = parts
    order_id = int(order_id_raw)
    driver_tg_id = int(driver_tg_id_raw)
    price = float(price_raw)
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
