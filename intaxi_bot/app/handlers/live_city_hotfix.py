from __future__ import annotations

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

import app.database.requests as rq
import app.keyboards as kb
from app.database.models import CityOrderV1, CityOrderRuntime, CityTripV1, DriverOnlineState, User, Vehicle, async_session
from app.hotfix_menu import home_webapp_menu
from app.miniapp_routes import current_trip_url
from app.strings import MESSAGES

router = Router()

LIVE_CITY_STATUSES = {"accepted", "driver_on_way", "driver_arrived", "in_progress"}
CITY_STATUS_NEXT = {
    "accepted": {"driver_on_way", "driver_arrived", "cancelled"},
    "driver_on_way": {"driver_arrived", "cancelled"},
    "driver_arrived": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
}


class CityCreateFlow(StatesGroup):
    pickup = State()
    destination = State()
    seats = State()
    price = State()
    comment = State()
    offer_price = State()


def _match_button(message_text: str | None, key: str) -> bool:
    if not message_text:
        return False
    for _, msgs in MESSAGES.items():
        if message_text == msgs.get(key):
            return True
    return False


def _current_trip_link(trip_id: int) -> str:
    base = current_trip_url().split("?", 1)[0]
    return f"{base}?tripType=city_trip&tripId={trip_id}"


def _trip_status_kb(trip_id: int, status: str, *, can_control: bool = False):
    builder = InlineKeyboardBuilder()
    builder.button(text="Open trip", url=_current_trip_link(trip_id))
    if can_control:
        if status in {"accepted", "driver_on_way"}:
            builder.button(text="Driver on way", callback_data=f"lctrip_onway_{trip_id}")
            builder.button(text="Arrived", callback_data=f"lctrip_arrived_{trip_id}")
        if status == "driver_arrived":
            builder.button(text="Start trip", callback_data=f"lctrip_start_{trip_id}")
        if status == "in_progress":
            builder.button(text="Complete trip", callback_data=f"lctrip_finish_{trip_id}")
    return builder.adjust(1).as_markup()


async def _vehicle_for_driver(driver_tg_id: int) -> Vehicle | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
        if not user:
            return None
        return await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(
        select(CityTripV1)
        .where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_CITY_STATUSES)))
        .order_by(CityTripV1.id.desc())
    )
    return trip is not None


async def _driver_can_receive_city_order(session, driver: User, order: CityOrderV1) -> bool:
    if not driver.is_verified or (driver.active_role or '') != 'driver' or driver.tg_id == order.creator_tg_id:
        return False
    online = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == driver.tg_id))
    if not online or not online.is_online:
        return False
    if order.country and online.country and online.country != order.country:
        return False
    if order.city and online.city and online.city != order.city:
        return False
    if await _driver_has_live_trip(session, driver.tg_id):
        return False
    return True


async def _notify_online_drivers(bot: Bot, order: CityOrderV1, runtime: CityOrderRuntime):
    async with async_session() as session:
        query = (
            select(User)
            .join(DriverOnlineState, DriverOnlineState.driver_tg_id == User.tg_id)
            .where(
                User.is_verified == True,
                User.active_role == 'driver',
                DriverOnlineState.is_online == True,
                User.tg_id != order.creator_tg_id,
            )
            .order_by(User.rating.desc(), User.rating_count.desc())
        )
        if order.country:
            query = query.where(DriverOnlineState.country == order.country)
        if order.city:
            query = query.where(DriverOnlineState.city == order.city)
        raw_drivers = (await session.scalars(query)).all()
        drivers = []
        for driver in raw_drivers:
            if await _driver_can_receive_city_order(session, driver, order):
                drivers.append(driver)
        runtime_row = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        if runtime_row:
            runtime_row.seen_by_drivers = len(drivers)
            await session.commit()
    for driver in drivers:
        kbld = InlineKeyboardBuilder()
        kbld.button(text="Accept", callback_data=f"lccacc_{order.id}")
        kbld.button(text="Offer price", callback_data=f"lccoffer_{order.id}")
        kbld.adjust(1)
        try:
            await bot.send_message(
                driver.tg_id,
                (
                    f"New city order\n\n"
                    f"A: {order.from_address}\n"
                    f"B: {order.to_address or '-'}\n"
                    f"Price: {order.price}\n"
                    f"Seats: {order.seats}\n"
                    f"Distance: {runtime.estimated_distance_km or '-'} km"
                ),
                reply_markup=kbld.as_markup(),
            )
        except Exception:
            pass


async def _send_trip_cards(bot: Bot, trip: CityTripV1):
    vehicle = await _vehicle_for_driver(trip.driver_tg_id)
    vehicle_text = "-"
    if vehicle:
        vehicle_text = f"{vehicle.brand or ''} {vehicle.model or ''}\nPlate: {vehicle.plate or '-'}\nColor: {vehicle.color or '-'}"
    passenger_text = (
        f"Driver found\n\n"
        f"A: {trip.from_address or '-'}\n"
        f"B: {trip.to_address or '-'}\n"
        f"Car:\n{vehicle_text}\n\n"
        f"Trip: {_current_trip_link(trip.id)}"
    )
    driver_text = (
        f"Order accepted\n\n"
        f"A: {trip.from_address or '-'}\n"
        f"B: {trip.to_address or '-'}\n"
        f"Trip: {_current_trip_link(trip.id)}"
    )
    try:
        await bot.send_message(trip.passenger_tg_id, passenger_text, reply_markup=_trip_status_kb(trip.id, trip.status, can_control=False))
    except Exception:
        pass
    try:
        await bot.send_message(trip.driver_tg_id, driver_text, reply_markup=_trip_status_kb(trip.id, trip.status, can_control=True))
    except Exception:
        pass


async def _notify_trip_status(bot: Bot, trip: CityTripV1, action: str):
    if action == 'onway':
        passenger_text = f"Driver is on the way.\n\nMini App: {_current_trip_link(trip.id)}"
        driver_text = f"Trip status updated: driver on way.\n\nMini App: {_current_trip_link(trip.id)}"
    elif action == 'arrived':
        passenger_text = f"Driver arrived.\n\nPickup: {trip.from_address or '-'}\nMini App: {_current_trip_link(trip.id)}"
        driver_text = f"You arrived.\n\nNext point: {trip.to_address or '-'}\nMini App: {_current_trip_link(trip.id)}"
    elif action == 'start':
        passenger_text = f"Trip started.\n\nNext point: {trip.to_address or '-'}\nMini App: {_current_trip_link(trip.id)}"
        driver_text = f"Trip started.\n\nNext point: {trip.to_address or '-'}\nMini App: {_current_trip_link(trip.id)}"
    else:
        passenger_text = "Trip completed. Thank you for using Intaxi."
        driver_text = "Trip completed."
    try:
        await bot.send_message(trip.passenger_tg_id, passenger_text, reply_markup=_trip_status_kb(trip.id, trip.status, can_control=False) if trip.status != 'completed' else None)
    except Exception:
        pass
    try:
        await bot.send_message(trip.driver_tg_id, driver_text, reply_markup=_trip_status_kb(trip.id, trip.status, can_control=True) if trip.status != 'completed' else None)
    except Exception:
        pass


@router.message(lambda message: _match_button(message.text, 'btn_fast_order'))
async def hotfix_city_create_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    if user.is_verified and (user.active_role or 'driver') != 'passenger':
        await state.clear()
        await message.answer('Drivers do not create city orders. Switch to passenger role in profile.', reply_markup=home_webapp_menu(lang, is_driver_mode=True))
        return
    await state.clear()
    await state.update_data(lang=lang, country=user.country or 'uz', city=user.city or '')
    await message.answer('Send pickup point or address.', reply_markup=kb.location_kb(lang))
    await state.set_state(CityCreateFlow.pickup)


@router.message(CityCreateFlow.pickup)
async def hotfix_city_pickup(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    pickup_address = (message.text or '').strip()
    pickup_lat = None
    pickup_lng = None
    if message.location:
        pickup_lat = float(message.location.latitude)
        pickup_lng = float(message.location.longitude)
        pickup_address = f"{pickup_lat:.6f},{pickup_lng:.6f}"
    if not pickup_address:
        await message.answer('Send pickup point or address.', reply_markup=kb.location_kb(lang))
        return
    await state.update_data(from_address=pickup_address, from_lat=pickup_lat, from_lng=pickup_lng)
    await message.answer('Send destination address or map point.', reply_markup=kb.destination_input_kb(lang))
    await state.set_state(CityCreateFlow.destination)


@router.message(CityCreateFlow.destination)
async def hotfix_city_destination(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    destination = (message.text or '').strip()
    to_lat = None
    to_lng = None
    if message.location:
        to_lat = float(message.location.latitude)
        to_lng = float(message.location.longitude)
        destination = f"{to_lat:.6f},{to_lng:.6f}"
    if not destination:
        await message.answer('Send destination text or map point without current-location button.', reply_markup=kb.destination_input_kb(lang))
        return
    await state.update_data(to_address=destination, to_lat=to_lat, to_lng=to_lng)
    await message.answer('How many passengers?', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CityCreateFlow.seats)


@router.message(CityCreateFlow.seats)
async def hotfix_city_seats(message: types.Message, state: FSMContext):
    try:
        seats = max(1, int((message.text or '1').strip()))
    except Exception:
        await message.answer('Enter seats as a number.')
        return
    await state.update_data(seats=seats)
    await message.answer('Enter your price as a number.')
    await state.set_state(CityCreateFlow.price)


@router.message(CityCreateFlow.price)
async def hotfix_city_price(message: types.Message, state: FSMContext):
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer('Enter price as a number.')
        return
    await state.update_data(price=price)
    await message.answer('Comment? Send - to skip.')
    await state.set_state(CityCreateFlow.comment)


@router.message(CityCreateFlow.comment)
async def hotfix_city_comment(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = data.get('lang', user.language or 'ru')
    comment = '' if (message.text or '').strip() == '-' else (message.text or '').strip()
    order, runtime = await rq.create_city_order_bot(
        creator_tg_id=user.tg_id,
        role='passenger',
        country=data.get('country', user.country or 'uz'),
        city=data.get('city', user.city or ''),
        from_address=data.get('from_address', ''),
        to_address=data.get('to_address', ''),
        seats=int(data.get('seats', 1)),
        price=float(data.get('price', 0)),
        comment=comment,
        from_lat=data.get('from_lat'),
        from_lng=data.get('from_lng'),
        to_lat=data.get('to_lat'),
        to_lng=data.get('to_lng'),
    )
    await state.clear()
    await message.answer('Order created. Active drivers were notified.', reply_markup=home_webapp_menu(lang, is_driver_mode=False))
    await _notify_online_drivers(bot, order, runtime)


@router.callback_query(F.data.startswith('lccacc_'))
async def hotfix_driver_accept(callback: types.CallbackQuery, bot: Bot):
    order_id = int(callback.data.split('_')[-1])
    trip = await rq.accept_city_offer_for_user(order_id, callback.from_user.id)
    if not trip:
        await callback.answer('Cannot accept order. Check online status and active trips.', show_alert=True)
        return
    await callback.answer('Order accepted')
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lccoffer_'))
async def hotfix_driver_offer_price(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split('_')[-1])
    async with async_session() as session:
        driver = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        if not driver or not order or not await _driver_can_receive_city_order(session, driver, order):
            await callback.answer('Order is not available for price offer', show_alert=True)
            return
    await state.set_state(CityCreateFlow.offer_price)
    await state.update_data(order_id=order_id, driver_tg_id=callback.from_user.id)
    await callback.message.answer('Enter your price for this order.')
    await callback.answer()


@router.message(CityCreateFlow.offer_price)
async def hotfix_driver_offer_price_submit(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer('Enter price as a number.')
        return
    order_id = int(data.get('order_id'))
    driver_tg_id = int(data.get('driver_tg_id'))
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        driver = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
        if not order or not driver or not await _driver_can_receive_city_order(session, driver, order):
            await state.clear()
            await message.answer('Order is no longer available.')
            return
    builder = InlineKeyboardBuilder()
    builder.button(text='Accept price', callback_data=f'lcpacc_{order_id}_{driver_tg_id}_{int(price)}')
    builder.button(text='Reject', callback_data=f'lcprej_{order_id}_{driver_tg_id}')
    builder.adjust(1)
    try:
        await bot.send_message(order.creator_tg_id, f'Driver offered price: {price}', reply_markup=builder.as_markup())
    except Exception:
        pass
    await state.clear()
    await message.answer('Price offer sent to passenger.')


@router.callback_query(F.data.startswith('lcpacc_'))
async def hotfix_passenger_accept_price(callback: types.CallbackQuery, bot: Bot):
    _, order_id, driver_tg_id, price = callback.data.split('_')
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == int(order_id)))
        if not order or order.creator_tg_id != callback.from_user.id:
            await callback.answer('Offer is not available', show_alert=True)
            return
        order.price = float(price)
        await session.commit()
    trip = await rq.accept_city_offer_for_user(int(order_id), int(driver_tg_id))
    if not trip:
        await callback.answer('Cannot accept offer', show_alert=True)
        return
    await callback.answer('Price accepted')
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lcprej_'))
async def hotfix_passenger_reject_price(callback: types.CallbackQuery, bot: Bot):
    _, order_id, driver_tg_id = callback.data.split('_')
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == int(order_id)))
        if order and order.creator_tg_id != callback.from_user.id:
            await callback.answer('This offer is not for you', show_alert=True)
            return
    try:
        await bot.send_message(int(driver_tg_id), f'Passenger rejected your price offer for order #{order_id}.')
    except Exception:
        pass
    await callback.answer('Offer rejected')


@router.message(lambda message: _match_button(message.text, 'btn_current_order'))
async def hotfix_current_trip(message: types.Message):
    trip = await rq.get_current_trip_for_user(message.from_user.id)
    if not isinstance(trip, CityTripV1):
        await message.answer('No active city order found now.')
        return
    vehicle = await _vehicle_for_driver(trip.driver_tg_id)
    vehicle_text = ''
    if vehicle:
        vehicle_text = f"\nCar: {vehicle.brand or ''} {vehicle.model or ''}\nPlate: {vehicle.plate or '-'}\nColor: {vehicle.color or '-'}"
    text = (
        f"Current order\n\n"
        f"A: {trip.from_address or '-'}\n"
        f"B: {trip.to_address or '-'}\n"
        f"Status: {trip.status}{vehicle_text}\n\n"
        f"Mini App: {_current_trip_link(trip.id)}"
    )
    await message.answer(text, reply_markup=_trip_status_kb(trip.id, trip.status, can_control=message.from_user.id == trip.driver_tg_id))


@router.callback_query(F.data.startswith('lctrip_'))
async def hotfix_trip_status(callback: types.CallbackQuery, bot: Bot):
    _, action, trip_id_raw = callback.data.split('_')
    trip_id = int(trip_id_raw)
    status_map = {
        'onway': 'driver_on_way',
        'arrived': 'driver_arrived',
        'start': 'in_progress',
        'finish': 'completed',
    }
    next_status = status_map.get(action)
    async with async_session() as session:
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == trip_id))
        if not trip:
            await callback.answer('Trip not found', show_alert=True)
            return
        if callback.from_user.id != trip.driver_tg_id:
            await callback.answer('Only the driver can update trip status', show_alert=True)
            return
        if not next_status or (next_status != trip.status and next_status not in CITY_STATUS_NEXT.get(trip.status, set())):
            await callback.answer('Invalid status transition', show_alert=True)
            return
        trip.status = next_status
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == trip.order_id))
        if order:
            order.status = next_status
        if next_status == 'completed':
            state = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == trip.driver_tg_id))
            if state:
                state.is_online = True
        await session.commit()
        await session.refresh(trip)
    await callback.answer('Status updated')
    await _notify_trip_status(bot, trip, action)
