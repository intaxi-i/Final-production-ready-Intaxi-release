from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

import app.database.requests as rq
import app.keyboards as kb
from app.database.models import CityOrderV1, CityOrderRuntime, CityTripV1, DriverOnlineState, User, Vehicle, async_session
from app.miniapp_routes import current_trip_url
from app.strings import MESSAGES

router = Router()
CITY_RADIUS_STAGES_KM = (3, 6, 12, 15)
LIVE_TRIP_STATUSES = {'accepted', 'driver_on_way', 'driver_arrived', 'in_progress'}
FINAL_TRIP_STATUSES = {'completed', 'cancelled'}
CITY_STATUS_NEXT = {
    'accepted': {'driver_on_way', 'driver_arrived', 'cancelled'},
    'driver_on_way': {'driver_arrived', 'cancelled'},
    'driver_arrived': {'in_progress', 'cancelled'},
    'in_progress': {'completed', 'cancelled'},
}

TEXTS = {
    'ru': {
        'accept': '✅ Принять', 'counteroffer': '💰 Предложить свою цену', 'new_order': '🆕 Новый городской заказ',
        'from': 'A', 'to': 'B', 'passenger_price': 'Цена пассажира', 'seats': 'Мест', 'trip_distance': 'Дистанция поездки', 'distance_to_passenger': 'До пассажира',
        'driver_found': '🚕 Водитель найден', 'order_accepted': '✅ Заказ принят', 'route': 'Маршрут', 'car': 'Автомобиль', 'plate': 'Номер', 'color': 'Цвет', 'open_trip': 'Открыть поездку',
        'onway_btn': '🚘 В пути', 'arrived_btn': '📍 Прибыл', 'start_btn': '▶️ Начать поездку', 'finish_btn': '✅ Завершить поездку', 'cancel_btn': '❌ Отменить поездку',
        'driver_on_way_p': '🚘 Водитель выехал к вам.', 'driver_on_way_d': '🚘 Вы выехали к пассажиру.',
        'driver_arrived_p': '📍 Водитель прибыл.', 'driver_arrived_d': '📍 Вы прибыли к пассажиру.',
        'trip_started_p': '▶️ Поездка началась.', 'trip_started_d': '▶️ Вы начали поездку.',
        'trip_finished_p': '✅ Поездка завершена. Спасибо, что воспользовались Intaxi.', 'trip_finished_d': '✅ Поездка завершена.',
        'trip_cancelled_p': '❌ Поездка отменена.', 'trip_cancelled_d': '❌ Поездка отменена.',
        'pickup_point': 'Точка встречи', 'next_point': 'Следующая точка', 'miniapp': 'Mini App',
        'pickup_prompt': 'Отметьте на карте точку A или отправьте адрес текстом.', 'destination_prompt': 'Отметьте на карте точку или напишите текстом ваш официальный адрес.',
        'destination_retry': 'Напишите конечный адрес текстом или отправьте точку без кнопки текущей геолокации.', 'seats_prompt': 'Сколько пассажиров?', 'seats_retry': 'Введите число мест.',
        'price_prompt': 'Укажите вашу цену цифрами.', 'price_retry': 'Введите цену цифрами.', 'comment_prompt': 'Комментарий к заказу? Можно отправить - для пропуска.',
        'created': '✅ Заказ создан. Активные водители получили его автоматически.', 'accept_failed': 'Не удалось принять заказ', 'accepted': 'Заказ принят',
        'offer_price_prompt': 'Введите вашу цену цифрами для этого заказа.', 'order_unavailable': 'Заказ уже недоступен.', 'accept_price': '✅ Принять цену', 'reject': '❌ Отклонить',
        'driver_offered_price': '💰 Водитель предложил свою цену', 'offer_sent': 'Предложение цены отправлено пассажиру.', 'offer_accept_failed': 'Не удалось принять предложение',
        'price_accepted': 'Цена принята', 'price_rejected_driver': '❌ Пассажир отклонил вашу цену по заказу', 'offer_rejected': 'Предложение отклонено',
        'no_active_trip': 'Активный городской заказ сейчас не найден.', 'current_order': '📌 Текущий заказ', 'status': 'Статус', 'trip_not_found': 'Поездка не найдена',
        'driver_only_status': 'Статус поездки может менять только водитель', 'invalid_transition': 'Недопустимый переход статуса', 'status_updated': 'Статус обновлён',
    },
    'uz': {
        'accept': '✅ Qabul qilish', 'counteroffer': '💰 O‘z narxini taklif qilish', 'new_order': '🆕 Yangi shahar buyurtmasi',
        'from': 'A', 'to': 'B', 'passenger_price': 'Yo‘lovchi narxi', 'seats': 'Joylar', 'trip_distance': 'Safar masofasi', 'distance_to_passenger': 'Yo‘lovchigacha',
        'driver_found': '🚕 Haydovchi topildi', 'order_accepted': '✅ Buyurtma qabul qilindi', 'route': 'Yo‘nalish', 'car': 'Avtomobil', 'plate': 'Raqam', 'color': 'Rang', 'open_trip': 'Safarni ochish',
        'onway_btn': '🚘 Yo‘ldaman', 'arrived_btn': '📍 Yetib keldim', 'start_btn': '▶️ Safarni boshlash', 'finish_btn': '✅ Safarni yakunlash', 'cancel_btn': '❌ Safarni bekor qilish',
        'driver_on_way_p': '🚘 Haydovchi siz tomonga yo‘lga chiqdi.', 'driver_on_way_d': '🚘 Siz yo‘lovchi tomonga yo‘lga chiqdingiz.',
        'driver_arrived_p': '📍 Haydovchi yetib keldi.', 'driver_arrived_d': '📍 Siz yo‘lovchi yoniga yetib keldingiz.',
        'trip_started_p': '▶️ Safar boshlandi.', 'trip_started_d': '▶️ Siz safarni boshladingiz.',
        'trip_finished_p': '✅ Safar yakunlandi. Intaxi xizmatidan foydalanganingiz uchun rahmat.', 'trip_finished_d': '✅ Safar yakunlandi.',
        'trip_cancelled_p': '❌ Safar bekor qilindi.', 'trip_cancelled_d': '❌ Safar bekor qilindi.',
        'pickup_point': 'Uchrashuv nuqtasi', 'next_point': 'Keyingi nuqta', 'miniapp': 'Mini App',
        'pickup_prompt': 'Xaritada A nuqtani belgilang yoki manzilni matn bilan yuboring.', 'destination_prompt': 'Xaritada nuqta belgilang yoki rasmiy manzilni matn bilan yozing.',
        'destination_retry': 'Oxirgi manzilni matn bilan yozing yoki joriy geolokatsiya tugmasisiz nuqta yuboring.', 'seats_prompt': 'Nechta yo‘lovchi?', 'seats_retry': 'Joylar sonini kiriting.',
        'price_prompt': 'Narxingizni raqam bilan kiriting.', 'price_retry': 'Narxni raqam bilan kiriting.', 'comment_prompt': 'Buyurtmaga izoh? O‘tkazib yuborish uchun - yuboring.',
        'created': '✅ Buyurtma yaratildi. Online haydovchilar uni avtomatik oldi.', 'accept_failed': 'Buyurtmani qabul qilib bo‘lmadi', 'accepted': 'Buyurtma qabul qilindi',
        'offer_price_prompt': 'Bu buyurtma uchun narxingizni raqam bilan kiriting.', 'order_unavailable': 'Buyurtma endi mavjud emas.', 'accept_price': '✅ Narxni qabul qilish', 'reject': '❌ Rad etish',
        'driver_offered_price': '💰 Haydovchi o‘z narxini taklif qildi', 'offer_sent': 'Narx taklifi yo‘lovchiga yuborildi.', 'offer_accept_failed': 'Taklifni qabul qilib bo‘lmadi',
        'price_accepted': 'Narx qabul qilindi', 'price_rejected_driver': '❌ Yo‘lovchi buyurtma bo‘yicha narxingizni rad etdi', 'offer_rejected': 'Taklif rad etildi',
        'no_active_trip': 'Hozir faol shahar buyurtmasi topilmadi.', 'current_order': '📌 Joriy buyurtma', 'status': 'Holat', 'trip_not_found': 'Safar topilmadi',
        'driver_only_status': 'Safar holatini faqat haydovchi o‘zgartiradi', 'invalid_transition': 'Holat o‘tishi noto‘g‘ri', 'status_updated': 'Holat yangilandi',
    },
    'en': {
        'accept': '✅ Accept', 'counteroffer': '💰 Offer your price', 'new_order': '🆕 New city order', 'from': 'A', 'to': 'B', 'passenger_price': 'Passenger price', 'seats': 'Seats', 'trip_distance': 'Trip distance', 'distance_to_passenger': 'To passenger',
        'driver_found': '🚕 Driver found', 'order_accepted': '✅ Order accepted', 'route': 'Route', 'car': 'Car', 'plate': 'Plate', 'color': 'Color', 'open_trip': 'Open trip',
        'onway_btn': '🚘 On my way', 'arrived_btn': '📍 Arrived', 'start_btn': '▶️ Start trip', 'finish_btn': '✅ Finish trip', 'cancel_btn': '❌ Cancel trip',
        'driver_on_way_p': '🚘 Driver is on the way.', 'driver_on_way_d': '🚘 You are on the way to the passenger.', 'driver_arrived_p': '📍 Driver arrived.', 'driver_arrived_d': '📍 You arrived at the passenger.', 'trip_started_p': '▶️ Trip started.', 'trip_started_d': '▶️ You started the trip.', 'trip_finished_p': '✅ Trip completed. Thanks for using Intaxi.', 'trip_finished_d': '✅ Trip completed.', 'trip_cancelled_p': '❌ Trip cancelled.', 'trip_cancelled_d': '❌ Trip cancelled.',
        'pickup_point': 'Pickup point', 'next_point': 'Next point', 'miniapp': 'Mini App', 'pickup_prompt': 'Mark point A on the map or send the address as text.', 'destination_prompt': 'Mark a point on the map or type the official address.', 'destination_retry': 'Type the destination address or send a point without the current location button.', 'seats_prompt': 'How many passengers?', 'seats_retry': 'Enter the number of seats.', 'price_prompt': 'Enter your price in digits.', 'price_retry': 'Enter the price in digits.', 'comment_prompt': 'Comment for the order? Send - to skip.',
        'created': '✅ Order created. Active drivers received it automatically.', 'accept_failed': 'Could not accept order', 'accepted': 'Order accepted', 'offer_price_prompt': 'Enter your price for this order in digits.', 'order_unavailable': 'Order is no longer available.', 'accept_price': '✅ Accept price', 'reject': '❌ Reject', 'driver_offered_price': '💰 Driver offered a price', 'offer_sent': 'Price offer sent to passenger.', 'offer_accept_failed': 'Could not accept offer', 'price_accepted': 'Price accepted', 'price_rejected_driver': '❌ Passenger rejected your price for order', 'offer_rejected': 'Offer rejected', 'no_active_trip': 'No active city order found.', 'current_order': '📌 Current order', 'status': 'Status', 'trip_not_found': 'Trip not found', 'driver_only_status': 'Only the driver can update trip status', 'invalid_transition': 'Invalid status transition', 'status_updated': 'Status updated',
    },
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _text(lang: str | None, key: str) -> str:
    code = (lang or 'ru').lower()
    if code not in TEXTS:
        code = 'ru'
    return TEXTS[code].get(key) or TEXTS['ru'].get(key) or key


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


def _driver_trip_status_kb(trip_id: int, status: str, lang: str | None = None):
    builder = InlineKeyboardBuilder()
    if status in {'accepted', 'driver_on_way'}:
        builder.button(text=_text(lang, 'onway_btn'), callback_data=f'lctrip_onway_{trip_id}')
        builder.button(text=_text(lang, 'arrived_btn'), callback_data=f'lctrip_arrived_{trip_id}')
    if status == 'driver_arrived':
        builder.button(text=_text(lang, 'start_btn'), callback_data=f'lctrip_start_{trip_id}')
    if status == 'in_progress':
        builder.button(text=_text(lang, 'finish_btn'), callback_data=f'lctrip_finish_{trip_id}')
    if status in LIVE_TRIP_STATUSES:
        builder.button(text=_text(lang, 'cancel_btn'), callback_data=f'lctrip_cancel_{trip_id}')
    return builder.adjust(1).as_markup() if builder.buttons else None


def _driver_distance(order_runtime: CityOrderRuntime, state: DriverOnlineState) -> float | None:
    if order_runtime.from_lat is None or order_runtime.from_lng is None or state.lat is None or state.lng is None:
        return None
    return round(rq.haversine_km(float(order_runtime.from_lat), float(order_runtime.from_lng), float(state.lat), float(state.lng)), 2)


async def _user_lang(session, tg_id: int, default: str = 'ru') -> str:
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return (user.language if user and user.language else default) or default


async def _vehicle_for_driver(driver_tg_id: int) -> Vehicle | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == driver_tg_id))
        if not user:
            return None
        return await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))


async def _driver_has_live_trip(session, driver_tg_id: int) -> bool:
    trip = await session.scalar(select(CityTripV1).where(CityTripV1.driver_tg_id == driver_tg_id, CityTripV1.status.in_(list(LIVE_TRIP_STATUSES))).order_by(CityTripV1.id.desc()))
    return trip is not None


async def _notify_online_drivers(bot: Bot, order: CityOrderV1, runtime: CityOrderRuntime):
    async with async_session() as session:
        states = (await session.scalars(select(DriverOnlineState).where(DriverOnlineState.is_online == True))).all()
        candidates: list[tuple[float | None, User]] = []
        for state in states:
            if order.country and state.country and state.country != order.country:
                continue
            if order.city and state.city and state.city != order.city:
                continue
            driver = await session.scalar(select(User).where(User.tg_id == state.driver_tg_id))
            if not driver or not driver.is_verified or driver.tg_id == order.creator_tg_id or (driver.active_role or '') != 'driver':
                continue
            if await _driver_has_live_trip(session, driver.tg_id):
                continue
            candidates.append((_driver_distance(runtime, state), driver))

        with_distance = [item for item in candidates if item[0] is not None]
        selected: list[tuple[float | None, User]] = []
        stage = 'manual_list'
        if with_distance:
            with_distance.sort(key=lambda item: item[0] or 10**9)
            for radius in CITY_RADIUS_STAGES_KM:
                selected = [item for item in with_distance if item[0] is not None and item[0] <= radius]
                if selected:
                    stage = f'{radius}km'
                    break
            if not selected:
                selected = with_distance
                stage = 'all_online'
        else:
            selected = candidates
            stage = 'active_drivers'

        runtime_row = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        if runtime_row:
            runtime_row.seen_by_drivers = len(selected)
            runtime_row.dispatch_stage = stage
            await session.commit()

    for distance, driver in selected:
        lang = driver.language or 'ru'
        kbld = InlineKeyboardBuilder()
        kbld.button(text=_text(lang, 'accept'), callback_data=f'lccacc_{order.id}')
        kbld.button(text=_text(lang, 'counteroffer'), callback_data=f'lccoffer_{order.id}')
        kbld.adjust(1)
        distance_line = f"\n{_text(lang, 'distance_to_passenger')}: {distance:.1f} km" if distance is not None else ''
        try:
            await bot.send_message(driver.tg_id, (
                f"{_text(lang, 'new_order')}\n\n"
                f"{_text(lang, 'from')}: {order.from_address or '—'}\n"
                f"{_text(lang, 'to')}: {order.to_address or '—'}\n"
                f"{_text(lang, 'passenger_price')}: {float(order.price or 0):g}\n"
                f"{_text(lang, 'seats')}: {order.seats}\n"
                f"{_text(lang, 'trip_distance')}: {runtime.estimated_distance_km or '—'} km"
                f"{distance_line}"
            ), reply_markup=kbld.as_markup())
        except Exception:
            pass


async def _send_trip_cards(bot: Bot, trip: CityTripV1):
    vehicle = await _vehicle_for_driver(trip.driver_tg_id)
    async with async_session() as session:
        passenger_lang = await _user_lang(session, trip.passenger_tg_id)
        driver_lang = await _user_lang(session, trip.driver_tg_id)
    vehicle_text = '—'
    if vehicle:
        vehicle_text = f"{vehicle.brand or ''} {vehicle.model or ''}\n{_text(passenger_lang, 'plate')}: {vehicle.plate or '—'}\n{_text(passenger_lang, 'color')}: {vehicle.color or '—'}"
    passenger_text = (
        f"{_text(passenger_lang, 'driver_found')}\n\n"
        f"{_text(passenger_lang, 'route')}: {trip.from_address or '—'} → {trip.to_address or '—'}\n"
        f"{_text(passenger_lang, 'car')}:\n{vehicle_text}\n\n"
        f"{_text(passenger_lang, 'open_trip')}: {_current_trip_link(trip.id)}"
    )
    driver_text = (
        f"{_text(driver_lang, 'order_accepted')}\n\n"
        f"{_text(driver_lang, 'route')}: {trip.from_address or '—'} → {trip.to_address or '—'}\n"
        f"{_text(driver_lang, 'open_trip')}: {_current_trip_link(trip.id)}"
    )
    try:
        await bot.send_message(trip.passenger_tg_id, passenger_text)
    except Exception:
        pass
    try:
        await bot.send_message(trip.driver_tg_id, driver_text, reply_markup=_driver_trip_status_kb(trip.id, trip.status, driver_lang))
    except Exception:
        pass


async def _notify_trip_status(bot: Bot, trip: CityTripV1, action: str):
    async with async_session() as session:
        passenger_lang = await _user_lang(session, trip.passenger_tg_id)
        driver_lang = await _user_lang(session, trip.driver_tg_id)
    if action == 'onway':
        passenger_text = f"{_text(passenger_lang, 'driver_on_way_p')}\n\n{_text(passenger_lang, 'miniapp')}: {_current_trip_link(trip.id)}"
        driver_text = f"{_text(driver_lang, 'driver_on_way_d')}\n\n{_text(driver_lang, 'miniapp')}: {_current_trip_link(trip.id)}"
    elif action == 'arrived':
        passenger_text = f"{_text(passenger_lang, 'driver_arrived_p')}\n\n{_text(passenger_lang, 'pickup_point')}: {trip.from_address or '—'}\n{_text(passenger_lang, 'miniapp')}: {_current_trip_link(trip.id)}"
        driver_text = f"{_text(driver_lang, 'driver_arrived_d')}\n\n{_text(driver_lang, 'next_point')}: {trip.to_address or '—'}\n{_text(driver_lang, 'miniapp')}: {_current_trip_link(trip.id)}"
    elif action == 'start':
        passenger_text = f"{_text(passenger_lang, 'trip_started_p')}\n\n{_text(passenger_lang, 'next_point')}: {trip.to_address or '—'}\n{_text(passenger_lang, 'miniapp')}: {_current_trip_link(trip.id)}"
        driver_text = f"{_text(driver_lang, 'trip_started_d')}\n\n{_text(driver_lang, 'next_point')}: {trip.to_address or '—'}\n{_text(driver_lang, 'miniapp')}: {_current_trip_link(trip.id)}"
    elif action == 'cancel':
        passenger_text = _text(passenger_lang, 'trip_cancelled_p')
        driver_text = _text(driver_lang, 'trip_cancelled_d')
    else:
        passenger_text = _text(passenger_lang, 'trip_finished_p')
        driver_text = _text(driver_lang, 'trip_finished_d')
    try:
        await bot.send_message(trip.passenger_tg_id, passenger_text)
    except Exception:
        pass
    try:
        await bot.send_message(trip.driver_tg_id, driver_text, reply_markup=_driver_trip_status_kb(trip.id, trip.status, driver_lang))
    except Exception:
        pass


@router.message(lambda message: _match_button(message.text, 'btn_fast_order'))
async def city_create_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.update_data(lang=lang, country=user.country or 'uz', city=user.city or '')
    await message.answer(_text(lang, 'pickup_prompt'), reply_markup=kb.location_kb(lang))
    await state.set_state(CityCreateFlow.pickup)


@router.message(CityCreateFlow.pickup)
async def city_pickup(message: types.Message, state: FSMContext):
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
        await message.answer(_text(lang, 'pickup_prompt'), reply_markup=kb.location_kb(lang))
        return
    await state.update_data(from_address=pickup_address, from_lat=pickup_lat, from_lng=pickup_lng)
    await message.answer(_text(lang, 'destination_prompt'), reply_markup=kb.destination_input_kb(lang))
    await state.set_state(CityCreateFlow.destination)


@router.message(CityCreateFlow.destination)
async def city_destination(message: types.Message, state: FSMContext):
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
        await message.answer(_text(lang, 'destination_retry'), reply_markup=kb.destination_input_kb(lang))
        return
    await state.update_data(to_address=destination, to_lat=to_lat, to_lng=to_lng)
    await message.answer(_text(lang, 'seats_prompt'), reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CityCreateFlow.seats)


@router.message(CityCreateFlow.seats)
async def city_seats(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    try:
        seats = max(1, int((message.text or '1').strip()))
    except Exception:
        await message.answer(_text(lang, 'seats_retry'))
        return
    await state.update_data(seats=seats)
    await message.answer(_text(lang, 'price_prompt'))
    await state.set_state(CityCreateFlow.price)


@router.message(CityCreateFlow.price)
async def city_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer(_text(lang, 'price_retry'))
        return
    await state.update_data(price=price)
    await message.answer(_text(lang, 'comment_prompt'))
    await state.set_state(CityCreateFlow.comment)


@router.message(CityCreateFlow.comment)
async def city_comment(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = data.get('lang', user.language or 'ru')
    comment = '' if (message.text or '').strip() == '-' else (message.text or '').strip()
    order, runtime = await rq.create_city_order_bot(creator_tg_id=user.tg_id, role='passenger', country=data.get('country', user.country or 'uz'), city=data.get('city', user.city or ''), from_address=data.get('from_address', ''), to_address=data.get('to_address', ''), seats=int(data.get('seats', 1)), price=float(data.get('price', 0)), comment=comment, from_lat=data.get('from_lat'), from_lng=data.get('from_lng'), to_lat=data.get('to_lat'), to_lng=data.get('to_lng'))
    await state.clear()
    await message.answer(_text(lang, 'created'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, is_driver_mode=False))
    await _notify_online_drivers(bot, order, runtime)


@router.callback_query(F.data.startswith('lccacc_'))
async def driver_accept(callback: types.CallbackQuery, bot: Bot):
    order_id = int(callback.data.split('_')[-1])
    trip = await rq.accept_city_offer_for_user(order_id, callback.from_user.id)
    async with async_session() as session:
        lang = await _user_lang(session, callback.from_user.id)
    if not trip:
        await callback.answer(_text(lang, 'accept_failed'), show_alert=True)
        return
    await callback.answer(_text(lang, 'accepted'))
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lccoffer_'))
async def driver_offer_price(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split('_')[-1])
    async with async_session() as session:
        lang = await _user_lang(session, callback.from_user.id)
    await state.set_state(CityCreateFlow.offer_price)
    await state.update_data(order_id=order_id, driver_tg_id=callback.from_user.id, lang=lang)
    await callback.message.answer(_text(lang, 'offer_price_prompt'))
    await callback.answer()


@router.message(CityCreateFlow.offer_price)
async def driver_offer_price_submit(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    try:
        price = float((message.text or '').replace(',', '.').strip())
    except Exception:
        await message.answer(_text(lang, 'price_retry'))
        return
    order_id = int(data.get('order_id'))
    driver_tg_id = int(data.get('driver_tg_id'))
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        passenger_lang = await _user_lang(session, order.creator_tg_id) if order else lang
    if not order:
        await state.clear()
        await message.answer(_text(lang, 'order_unavailable'))
        return
    builder = InlineKeyboardBuilder()
    builder.button(text=_text(passenger_lang, 'accept_price'), callback_data=f'lcpacc_{order_id}_{driver_tg_id}_{int(price)}')
    builder.button(text=_text(passenger_lang, 'reject'), callback_data=f'lcprej_{order_id}_{driver_tg_id}')
    builder.adjust(1)
    try:
        await bot.send_message(order.creator_tg_id, f"{_text(passenger_lang, 'driver_offered_price')}: {price}", reply_markup=builder.as_markup())
    except Exception:
        pass
    await state.clear()
    await message.answer(_text(lang, 'offer_sent'))


@router.callback_query(F.data.startswith('lcpacc_'))
async def passenger_accept_price(callback: types.CallbackQuery, bot: Bot):
    _, order_id, driver_tg_id, price = callback.data.split('_')
    async with async_session() as session:
        lang = await _user_lang(session, callback.from_user.id)
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == int(order_id)))
        if order:
            order.price = float(price)
            await session.commit()
    trip = await rq.accept_city_offer_for_user(int(order_id), int(driver_tg_id))
    if not trip:
        await callback.answer(_text(lang, 'offer_accept_failed'), show_alert=True)
        return
    await callback.answer(_text(lang, 'price_accepted'))
    await _send_trip_cards(bot, trip)


@router.callback_query(F.data.startswith('lcprej_'))
async def passenger_reject_price(callback: types.CallbackQuery, bot: Bot):
    _, order_id, driver_tg_id = callback.data.split('_')
    async with async_session() as session:
        passenger_lang = await _user_lang(session, callback.from_user.id)
        driver_lang = await _user_lang(session, int(driver_tg_id))
    try:
        await bot.send_message(int(driver_tg_id), f"{_text(driver_lang, 'price_rejected_driver')} #{order_id}.")
    except Exception:
        pass
    await callback.answer(_text(passenger_lang, 'offer_rejected'))


@router.message(lambda message: _match_button(message.text, 'btn_current_order'))
async def current_trip(message: types.Message):
    trip = await rq.get_current_trip_for_user(message.from_user.id)
    async with async_session() as session:
        lang = await _user_lang(session, message.from_user.id)
    if not isinstance(trip, CityTripV1):
        await message.answer(_text(lang, 'no_active_trip'))
        return
    vehicle = await _vehicle_for_driver(trip.driver_tg_id)
    vehicle_text = ''
    if vehicle:
        vehicle_text = f"\n{_text(lang, 'car')}: {vehicle.brand or ''} {vehicle.model or ''}\n{_text(lang, 'plate')}: {vehicle.plate or '—'}\n{_text(lang, 'color')}: {vehicle.color or '—'}"
    text = (
        f"{_text(lang, 'current_order')}\n\n"
        f"A: {trip.from_address or '—'}\n"
        f"B: {trip.to_address or '—'}\n"
        f"{_text(lang, 'status')}: {trip.status}{vehicle_text}\n\n"
        f"{_text(lang, 'miniapp')}: {_current_trip_link(trip.id)}"
    )
    reply_markup = _driver_trip_status_kb(trip.id, trip.status, lang) if message.from_user.id == trip.driver_tg_id else None
    await message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith('lctrip_'))
async def trip_status(callback: types.CallbackQuery, bot: Bot):
    _, action, trip_id_raw = callback.data.split('_')
    trip_id = int(trip_id_raw)
    status_map = {'onway': 'driver_on_way', 'arrived': 'driver_arrived', 'start': 'in_progress', 'finish': 'completed', 'cancel': 'cancelled'}
    next_status = status_map.get(action)
    async with async_session() as session:
        lang = await _user_lang(session, callback.from_user.id)
        trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == trip_id))
        if not trip:
            await callback.answer(_text(lang, 'trip_not_found'), show_alert=True)
            return
        if callback.from_user.id != trip.driver_tg_id:
            await callback.answer(_text(lang, 'driver_only_status'), show_alert=True)
            return
        if not next_status or next_status not in CITY_STATUS_NEXT.get(trip.status, set()):
            await callback.answer(_text(lang, 'invalid_transition'), show_alert=True)
            return
        trip.status = next_status
        trip.updated_at = _now()
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == trip.order_id))
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == trip.order_id))
        if next_status == 'completed':
            trip.completed_at = _now()
            if order:
                order.status = 'completed'
            if runtime:
                runtime.active_trip_id = None
        elif next_status == 'cancelled':
            trip.cancelled_at = _now()
            if order:
                order.status = 'cancelled'
            if runtime:
                runtime.active_trip_id = None
        await session.commit()
        await session.refresh(trip)
    await callback.answer(_text(lang, 'status_updated'))
    await _notify_trip_status(bot, trip, action)
