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


def _trip_status_kb(trip_id: int, status: str):
    builder = InlineKeyboardBuilder()
    if status in {"accepted", "driver_on_way"}:
        builder.button(text="🚘 В пути", callback_data=f"lctrip_onway_{trip_id}")
        builder.button(text="📍 Прибыл", callback_data=f"lctrip_arrived_{trip_id}")
    if status == "driver_arrived":
        builder.button(text="▶️ Начать поездку", callback_data=f"lctrip_start_{trip_id}")
    if status == "in_progress":
        builder.button(text="✅ Завершить поездку", callback_data=f"lctrip_finish_{trip_id}")
    return builder.adjust(1).as_markup()


async def _vehicle_for_driver(driver_tg_id: int) -> Vehicle | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
        if not user:
            return None
        return await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))


async def _notify_online_drivers(bot: Bot, order: CityOrderV1, runtime: CityOrderRuntime):
    async with async_session() as session:
        query = (
            select(User)
            .join(DriverOnlineState, DriverOnlineState.driver_tg_id == User.tg_id)
            .where(
                User.is_verified == True,
                DriverOnlineState.is_online == True,
                User.tg_id != order.creator_tg_id,
            )
            .order_by(User.rating.desc(), User.rating_count.desc())
        )
        if order.country:
            query = query.where(DriverOnlineState.country == order.country)
        if order.city:
            query = query.where(DriverOnlineState.city == order.city)
        drivers = (await session.scalars(query)).all()
        runtime_row = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        if runtime_row:
            runtime_row.seen_by_drivers = len(drivers)
            await session.commit()
    for driver in drivers:
        kbld = InlineKeyboardBuilder()
        kbld.button(text="✅ Принять", callback_data=f"lccacc_{order.id}")
        kbld.button(text="💰 Предложить свою цену", callback_data=f"lccoffer_{order.id}")
        kbld.adjust(1)
        try:
            await bot.send_message(
                driver.tg_id,
                (
                    f"🆕 Новый заказ\n\n"
                    f"A: {order.from_address}\n"
                    f"B: {order.to_address or '—'}\n"
                    f"Цена: {order.price}\n"
                    f"Мест: {order.seats}\n"
                    f"Расстояние: {runtime.estimated_distance_km or '—'} km"
                ),
                reply_markup=kbld.as_markup(),
            )
        except Exception:
            pass


async def _send_trip_cards(bot: Bot, trip: CityTripV1):
    vehicle = await _vehicle_for_driver(trip.driver_tg_id)
    vehicle_text = "—"
    if vehicle:
        vehicle_text = f"{vehicle.brand or ''} {vehicle.model or ''}\nНомер: {vehicle.plate or '—'}\nЦвет: {vehicle.color or '—'}"
    passenger_text = (
        f"🚕 Водитель найден\n\n"
        f"Маршрут: {trip.from_address or '—'} → {trip.to_address or '—'}\n"
        f"Автомобиль:\n{vehicle_text}\n\n"
        f"Открыть поездку: {_current_trip_link(trip.id)}"
    )
    driver_text = (
        f"✅ Заказ принят\n\n"
        f"Маршрут: {trip.from_address or '—'} → {trip.to_address or '—'}\n"
        f"Открыть поездку: {_current_trip_link(trip.id)}"
    )
    try:
        await bot.send_message(trip.passenger_tg_id, passenger_text, reply_markup=_trip_status_kb(trip.id, trip.status))
    except Exception:
        pass
    try:
        await bot.send_message(trip.driver_tg_id, driver_text, reply_markup=_trip_status_kb(trip.id, trip.status))
    except Exception:
        pass


async def _notify_trip_status(bot: Bot, trip: CityTripV1, action: str):
    if action == 'onway':
        passenger_text = f"🚘 Водитель выехал к вам.\n\nМини App: {_current_trip_link(trip.id)}"
        driver_text = f"🚘 Статус поездки обновлён: водитель в пути.\n\nМини App: {_current_trip_link(trip.id)}"
    elif action == 'arrived':
        passenger_text = f"📍 Водитель прибыл.\n\nТочка встречи: {trip.from_address or '—'}\nMini App: {_current_trip_link(trip.id)}"
        driver_text = f"📍 Вы прибыли.\n\nСледующая точка: {trip.to_address or '—'}\nMini App: {_current_trip_link(trip.id)}"
    elif action == 'start':
        passenger_text = f"▶️ Поездка началась.\n\nСледующая точка: {trip.to_address or '—'}\nMini App: {_current_trip_link(trip.id)}"
        driver_text = f"▶️ Поездка началась.\n\nСледующая точка: {trip.to_address or '—'}\nMini App: {_current_trip_link(trip.id)}"
    else:
        passenger_text = f"✅ Поездка завершена.\n\nСпасибо, что воспользовались Intaxi."
        driver_text = f"✅ Поездка завершена."
    try:
        await bot.send_message(trip.passenger_tg_id, passenger_text, reply_markup=_trip_status_kb(trip.id, trip.status))
    except Exception:
        pass
    try:
        await bot.send_message(trip.driver_tg_id, driver_text, reply_markup=_trip_status_kb(trip.id, trip.status))
    except Exception:
        pass


@router.message(lambda message: _match_button(message.text, 'btn_fast_order'))
async def hotfix_city_create_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.update_data(lang=lang, country=user.country or 'uz', city=user.city or '')
    await message.answer('Отметьте на карте точку A или отправьте адрес текстом.', reply_markup=kb.location_kb(lang))
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
        await message.answer('Отметьте на карте точку A или отправьте адрес текстом.', reply_markup=kb.location_kb(lang))
        return
    await state.update_data(from_address=pickup_address, from_lat=pickup_lat, from_lng=pickup_lng)
    await message.answer('Отметьте на карте точку или напишите текстом ваш официальный адрес.', reply_markup=kb.destination_input_kb(lang))
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
        await message.answer('Напишите конечный адрес текстом или отправьте точку без кнопки текущей геолокации.', reply_markup=kb.destination_input_kb(lang))
        return
    await state.update_data(to_address=destination, to_lat=to_lat, to_lng=to_lng)
    await message.answer('Сколько пассажиров?', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CityCreateFlow.seats)


@router.message(CityCreateFlow.seats)
async def hotfix_city_seats(message: types.Message, state: FSMContext):
    try:
        seats = max(1, int((message.text or '1').strip()))
    except Exception:
        await message.answer('Введите число мест.')
        return
    await state.update_data(seats=seats)
    await message.answer('Укажите вашу цену цифрами.')
    await state.set_state(CityCreateFlow.price)


@router.message(CityCreateFlow.price)
async def hotfix_city_price(message: types.Message, state: FSMContext):
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer('Введите цену цифрами.')
        return
    await state.update_data(price=price)
    await message.answer('Комментарий к заказу? Можно отправить - для пропуска.')
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
    await message.answer('✅ Заказ создан. Активные водители получили его автоматически.', reply_markup=home_webapp_menu(lang, is_driver_mode=False))
    await _notify_online_drivers(bot, order, runtime)


@router.callback_query(F.data.startswith('lccacc_'))
async def hotfix_driver_accept(callback: types.CallbackQuery, bot: Bot):
    order_id = int(callback.data.split('_')[-1])
    trip = await rq.accept_city_offer_for_user(order_id, callback.from_user.id)
    if not trip:
        await callback.answer('Не удалось принять заказ', show_alert=True)
        return
    await callback.answer('Заказ принят')
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lccoffer_'))
async def hotfix_driver_offer_price(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split('_')[-1])
    await state.set_state(CityCreateFlow.offer_price)
    await state.update_data(order_id=order_id, driver_tg_id=callback.from_user.id)
    await callback.message.answer('Введите вашу цену цифрами для этого заказа.')
    await callback.answer()


@router.message(CityCreateFlow.offer_price)
async def hotfix_driver_offer_price_submit(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer('Введите цену цифрами.')
        return
    order_id = int(data.get('order_id'))
    driver_tg_id = int(data.get('driver_tg_id'))
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
    if not order:
        await state.clear()
        await message.answer('Заказ уже недоступен.')
        return
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Принять цену', callback_data=f'lcpacc_{order_id}_{driver_tg_id}_{int(price)}')
    builder.button(text='❌ Отклонить', callback_data=f'lcprej_{order_id}_{driver_tg_id}')
    builder.adjust(1)
    try:
        await bot.send_message(order.creator_tg_id, f'💰 Водитель предложил свою цену: {price}', reply_markup=builder.as_markup())
    except Exception:
        pass
    await state.clear()
    await message.answer('Предложение цены отправлено пассажиру.')


@router.callback_query(F.data.startswith('lcpacc_'))
async def hotfix_passenger_accept_price(callback: types.CallbackQuery, bot: Bot):
    _, order_id, driver_tg_id, price = callback.data.split('_')
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == int(order_id)))
        if order:
            order.price = float(price)
            await session.commit()
    trip = await rq.accept_city_offer_for_user(int(order_id), int(driver_tg_id))
    if not trip:
        await callback.answer('Не удалось принять предложение', show_alert=True)
        return
    await callback.answer('Цена принята')
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lcprej_'))
async def hotfix_passenger_reject_price(callback: types.CallbackQuery, bot: Bot):
    _, order_id, driver_tg_id = callback.data.split('_')
    try:
        await bot.send_message(int(driver_tg_id), f'❌ Пассажир отклонил вашу цену по заказу #{order_id}.')
    except Exception:
        pass
    await callback.answer('Предложение отклонено')


@router.message(lambda message: _match_button(message.text, 'btn_current_order'))
async def hotfix_current_trip(message: types.Message):
    trip = await rq.get_current_trip_for_user(message.from_user.id)
    if not isinstance(trip, CityTripV1):
        await message.answer('Активный городской заказ сейчас не найден.')
        return
    vehicle = await _vehicle_for_driver(trip.driver_tg_id)
    vehicle_text = ''
    if vehicle:
        vehicle_text = f"\nАвто: {vehicle.brand or ''} {vehicle.model or ''}\nНомер: {vehicle.plate or '—'}\nЦвет: {vehicle.color or '—'}"
    text = (
        f"📌 Текущий заказ\n\n"
        f"A: {trip.from_address or '—'}\n"
        f"B: {trip.to_address or '—'}\n"
        f"Статус: {trip.status}{vehicle_text}\n\n"
        f"Мини App: {_current_trip_link(trip.id)}"
    )
    await message.answer(text, reply_markup=_trip_status_kb(trip.id, trip.status))


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
            await callback.answer('Поездка не найдена', show_alert=True)
            return
        trip.status = next_status or trip.status
        await session.commit()
        await session.refresh(trip)
    await callback.answer('Статус обновлён')
    await _notify_trip_status(bot, trip, action)
