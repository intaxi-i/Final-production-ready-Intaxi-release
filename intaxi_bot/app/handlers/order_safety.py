from __future__ import annotations

import html

from aiogram import F, Bot, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.database.requests as rq
import app.keyboards as kb
import app.order_actions as order_actions
from app.miniapp_routes import city_create_url, city_main_url, current_trip_url, intercity_main_url, intercity_request_url, intercity_route_url
from app.strings import MESSAGES

router = Router()

TEXTS = {
    'ru': {
        'current_trip': '📌 Текущая поездка', 'open_city': 'Открыть город', 'open_intercity': 'Открыть межгород',
        'moved_to_miniapp': 'Этот сценарий переведён в Mini App. Откройте актуальный раздел ниже.',
        'complaint_prompt': 'Напишите жалобу одним сообщением. Она будет отправлена администраторам.',
        'complaint_new': 'Новая жалоба', 'from_user': 'От', 'target': 'Цель', 'text': 'Текст', 'complaint_sent': '✅ Жалоба отправлена.',
        'not_found': 'Не найдено или нет доступа', 'city_order_closed': 'Городской заказ #{id} закрыт.',
        'empty': 'Сейчас активных предложений не найдено.', 'accept': '✅ Принять', 'price': 'Цена', 'status': 'Статус',
        'distance': 'До пассажира', 'created_by': 'Создатель', 'current_trip_open': 'Открыть текущую поездку', 'accepted': '✅ Заказ принят',
        'date': 'Дата', 'time': 'Время', 'seats': 'Мест', 'route': 'Маршрут', 'request': 'Заявка',
    },
    'uz': {
        'current_trip': '📌 Joriy safar', 'open_city': 'Shaharni ochish', 'open_intercity': 'Shaharlararoni ochish',
        'moved_to_miniapp': 'Bu ssenariy Mini Appga o‘tkazilgan. Quyidagi aktual bo‘limni oching.',
        'complaint_prompt': 'Shikoyatni bitta xabar bilan yozing. U administratorlarga yuboriladi.',
        'complaint_new': 'Yangi shikoyat', 'from_user': 'Kimdan', 'target': 'Maqsad', 'text': 'Matn', 'complaint_sent': '✅ Shikoyat yuborildi.',
        'not_found': 'Topilmadi yoki ruxsat yo‘q', 'city_order_closed': 'Shahar buyurtmasi #{id} yopildi.',
        'empty': 'Hozir faol takliflar yo‘q.', 'accept': '✅ Qabul qilish', 'price': 'Narx', 'status': 'Holat',
        'distance': 'Yo‘lovchigacha', 'created_by': 'Yaratgan', 'current_trip_open': 'Joriy safarni ochish', 'accepted': '✅ Buyurtma qabul qilindi',
        'date': 'Sana', 'time': 'Vaqt', 'seats': 'Joylar', 'route': 'Yo‘nalish', 'request': 'Zayavka',
    },
    'en': {
        'current_trip': '📌 Current trip', 'open_city': 'Open city', 'open_intercity': 'Open intercity',
        'moved_to_miniapp': 'This scenario has been moved to the Mini App. Open the current section below.',
        'complaint_prompt': 'Send your complaint in one message. It will be forwarded to the admins.',
        'complaint_new': 'New complaint', 'from_user': 'From', 'target': 'Target', 'text': 'Text', 'complaint_sent': '✅ Complaint sent.',
        'not_found': 'Not found or access denied', 'city_order_closed': 'City order #{id} has been closed.',
        'empty': 'No active offers right now.', 'accept': '✅ Accept', 'price': 'Price', 'status': 'Status',
        'distance': 'To passenger', 'created_by': 'Created by', 'current_trip_open': 'Open current trip', 'accepted': '✅ Order accepted',
        'date': 'Date', 'time': 'Time', 'seats': 'Seats', 'route': 'Route', 'request': 'Request',
    },
    'ar': {
        'current_trip': '📌 الرحلة الحالية', 'open_city': 'فتح المدينة', 'open_intercity': 'فتح بين المدن',
        'moved_to_miniapp': 'تم نقل هذا السيناريو إلى Mini App. افتح القسم الحالي أدناه.',
        'complaint_prompt': 'اكتب الشكوى في رسالة واحدة. سيتم إرسالها إلى المشرفين.',
        'complaint_new': 'شكوى جديدة', 'from_user': 'من', 'target': 'الهدف', 'text': 'النص', 'complaint_sent': '✅ تم إرسال الشكوى.',
        'not_found': 'غير موجود أو لا توجد صلاحية', 'city_order_closed': 'تم إغلاق طلب المدينة #{id}.',
        'empty': 'لا توجد عروض نشطة الآن.', 'accept': '✅ قبول', 'price': 'السعر', 'status': 'الحالة',
        'distance': 'إلى الراكب', 'created_by': 'أنشأه', 'current_trip_open': 'فتح الرحلة الحالية', 'accepted': '✅ تم قبول الطلب',
        'date': 'التاريخ', 'time': 'الوقت', 'seats': 'المقاعد', 'route': 'المسار', 'request': 'الطلب',
    },
}

UNSUPPORTED_INLINE_PREFIXES = (
    'acc_', 'acceptoffer_', 'arrived_', 'cancelsearch_', 'coming_', 'drv_offer_price_',
    'finish_', 'icarrived_', 'iccoming_', 'icdetail_', 'icfinish_', 'icreqprice_',
    'icreqtime_', 'icroffer_', 'icrsel_', 'icstart_', 'idreqacc_', 'idreqrej_',
    'intacc_', 'passdestnote_', 'passpicknote_', 'passprice_', 'passstop_', 'passtime_',
    'payintercity_', 'payorder_', 'rate_', 'rejectoffer_', 'routeprice_', 'routetime_',
    'intercity_common_cancel',
)


def _t(lang: str | None, key: str) -> str:
    code = (lang or 'ru').lower()
    if code not in TEXTS:
        code = 'ru'
    return TEXTS[code].get(key) or TEXTS['ru'].get(key) or key


class ComplaintFlow(StatesGroup):
    waiting_text = State()


async def _notify_targets(bot: Bot, permission: str, text: str) -> None:
    for admin_id in await rq.get_admin_targets_by_permission(permission):
        try:
            await bot.send_message(admin_id, text, parse_mode='HTML', disable_web_page_preview=True)
        except Exception:
            pass


def _recovery_markup(lang: str, callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'current_trip'), web_app=types.WebAppInfo(url=current_trip_url()))
    if callback_data.startswith(('ic', 'int', 'route', 'intercity_')) or 'intercity' in callback_data:
        builder.button(text=_t(lang, 'open_intercity'), web_app=types.WebAppInfo(url=intercity_main_url()))
    else:
        builder.button(text=_t(lang, 'open_city'), web_app=types.WebAppInfo(url=city_main_url()))
    return builder.adjust(1).as_markup()


def _create_markup(lang: str, callback_data: str):
    builder = InlineKeyboardBuilder()
    if callback_data == 'citybot_create_driver':
        builder.button(text=_t(lang, 'open_city'), web_app=types.WebAppInfo(url=city_create_url('driver')))
    elif callback_data == 'citybot_create_passenger':
        builder.button(text=_t(lang, 'open_city'), web_app=types.WebAppInfo(url=city_create_url('passenger')))
    elif callback_data == 'interbot_create_route':
        builder.button(text=_t(lang, 'open_intercity'), web_app=types.WebAppInfo(url=intercity_route_url()))
    else:
        builder.button(text=_t(lang, 'open_intercity'), web_app=types.WebAppInfo(url=intercity_request_url()))
    return builder.adjust(1).as_markup()


def _intercity_text(row, lang: str, kind: str) -> str:
    from_city = html.escape(getattr(row, 'from_city', None) or '—')
    to_city = html.escape(getattr(row, 'to_city', None) or '—')
    date = html.escape(getattr(row, 'departure_date', None) or getattr(row, 'desired_date', None) or '—')
    time = html.escape(getattr(row, 'departure_time', None) or getattr(row, 'desired_time', None) or '—')
    seats = html.escape(str(getattr(row, 'seats', None) or getattr(row, 'seats_needed', None) or '—'))
    price = float(getattr(row, 'price', None) or getattr(row, 'price_offer', None) or 0)
    return (
        f"<b>{_t(lang, kind)} #{row.id}</b>\n"
        f"{from_city} → {to_city}\n"
        f"{_t(lang, 'date')}: {date}\n"
        f"{_t(lang, 'time')}: {time}\n"
        f"{_t(lang, 'seats')}: {seats}\n"
        f"{_t(lang, 'price')}: {price:g}"
    )


@router.callback_query(F.data.in_({'citybot_create_passenger', 'citybot_create_driver', 'interbot_create_route', 'interbot_create_request'}))
async def safe_create_flow(callback: types.CallbackQuery):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await callback.message.answer(_t(lang, 'moved_to_miniapp'), reply_markup=_create_markup(lang, callback.data or ''))
    await callback.answer()


@router.callback_query(F.data.in_({'interbot_list_routes', 'interbot_list_requests'}))
async def safe_intercity_market(callback: types.CallbackQuery):
    kind = 'route' if callback.data == 'interbot_list_routes' else 'request'
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    rows = await order_actions.list_intercity_market_for_user(user.tg_id, kind=kind, limit=10)
    if not rows:
        await callback.message.answer(_t(lang, 'empty'))
        await callback.answer()
        return
    for row in rows:
        builder = InlineKeyboardBuilder()
        if kind == 'route':
            builder.button(text=_t(lang, 'accept'), callback_data=f'interbot_accept_route_{row.id}')
        else:
            builder.button(text=_t(lang, 'accept'), callback_data=f'interbot_accept_request_{row.id}')
        await callback.message.answer(_intercity_text(row, lang, kind), reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('interbot_accept_route_'))
async def safe_intercity_accept_route(callback: types.CallbackQuery):
    item_id = int((callback.data or '').rsplit('_', 1)[1])
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    row = await order_actions.accept_intercity_offer_for_user(kind='route', item_id=item_id, tg_id=user.tg_id)
    if not row:
        await callback.answer(_t(lang, 'not_found'), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'current_trip_open'), web_app=types.WebAppInfo(url=current_trip_url(trip_type='intercity_route', trip_id=row.id)))
    await callback.message.answer(f"{_t(lang, 'accepted')}\n{_intercity_text(row, lang, 'route')}", reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer('OK')


@router.callback_query(F.data.startswith('interbot_accept_request_'))
async def safe_intercity_accept_request(callback: types.CallbackQuery):
    item_id = int((callback.data or '').rsplit('_', 1)[1])
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    row = await order_actions.accept_intercity_offer_for_user(kind='request', item_id=item_id, tg_id=user.tg_id)
    if not row:
        await callback.answer(_t(lang, 'not_found'), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'current_trip_open'), web_app=types.WebAppInfo(url=current_trip_url(trip_type='intercity_request', trip_id=row.id)))
    await callback.message.answer(f"{_t(lang, 'accepted')}\n{_intercity_text(row, lang, 'request')}", reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer('OK')


@router.callback_query(F.data.in_({'citybot_list_driver', 'citybot_list_passenger'}))
async def safe_city_market(callback: types.CallbackQuery):
    wanted_role = 'driver' if callback.data == 'citybot_list_driver' else 'passenger'
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    items = await order_actions.list_city_market_for_user(user.tg_id, wanted_role=wanted_role, limit=10)
    if not items:
        await callback.message.answer(_t(lang, 'empty'))
        await callback.answer()
        return
    for item in items:
        row = item['order']
        creator = item.get('creator')
        vehicle = item.get('vehicle')
        distance = item.get('driver_distance_km')
        safe_from = html.escape(row.from_address or '—')
        safe_to = html.escape(row.to_address or '—')
        text = (
            f"<b>{html.escape(row.city or '—')}</b>\n"
            f"#{row.id} · {safe_from} → {safe_to}\n"
            f"{_t(lang, 'price')}: {float(row.price or 0):g}\n"
        )
        if distance is not None:
            text += f"{_t(lang, 'distance')}: {distance:.1f} km\n"
        if creator:
            text += f"{_t(lang, 'created_by')}: {html.escape(creator.full_name or str(creator.tg_id))}\n"
        if vehicle:
            text += f"🚗 {html.escape((vehicle.brand or '') + ' ' + (vehicle.model or '') + ' ' + (vehicle.plate or '')).strip()}\n"
        builder = InlineKeyboardBuilder()
        builder.button(text=_t(lang, 'accept'), callback_data=f'citybot_accept_{row.id}')
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('citybot_accept_'))
async def safe_city_accept(callback: types.CallbackQuery):
    order_id = int((callback.data or '').rsplit('_', 1)[1])
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    trip = await order_actions.accept_city_offer_for_user(order_id, user.tg_id)
    if not trip:
        await callback.answer(_t(lang, 'not_found'), show_alert=True)
        return
    text = (
        f"{_t(lang, 'accepted')}\n"
        f"#{trip.id}\n"
        f"{html.escape(trip.from_address or '—')} → {html.escape(trip.to_address or '—')}\n"
        f"{_t(lang, 'price')}: {float(trip.price or 0):g}\n"
        f"{_t(lang, 'status')}: {html.escape(trip.status or 'accepted')}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'current_trip_open'), web_app=types.WebAppInfo(url=current_trip_url()))
    await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer('OK')


@router.callback_query(F.data.startswith('cancl_'))
async def close_city_order(callback: types.CallbackQuery):
    order_id = int((callback.data or '').rsplit('_', 1)[1])
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    row = await order_actions.close_city_order_for_user(order_id, callback.from_user.id)
    if not row:
        await callback.answer(_t(lang, 'not_found'), show_alert=True)
        return
    await callback.message.answer(_t(lang, 'city_order_closed').format(id=order_id))
    await callback.answer('OK')


@router.callback_query(F.data.startswith(UNSUPPORTED_INLINE_PREFIXES))
async def safe_legacy_recovery(callback: types.CallbackQuery):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await callback.message.answer(_t(lang, 'moved_to_miniapp'), reply_markup=_recovery_markup(lang, callback.data or ''))
    await callback.answer()


@router.callback_query(F.data.startswith(('compl_city_driver_', 'compl_city_passenger_', 'compl_intercity_driver_', 'compl_intercity_passenger_')))
async def complaint_start(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.set_state(ComplaintFlow.waiting_text)
    await state.update_data(complaint_target=callback.data)
    await callback.message.answer(_t(lang, 'complaint_prompt'))
    await callback.answer()


@router.message(ComplaintFlow.waiting_text)
async def complaint_finish(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    target = data.get('complaint_target', '-')
    body = (message.text or '').strip()
    entry = await rq.create_feedback_entry(user.tg_id, 'complaint', 'text', text_value=body)
    safe_name = html.escape(user.full_name or '—')
    safe_username = html.escape(user.username or '—')
    safe_target = html.escape(str(target or '—'))
    safe_body = html.escape(body or '—')
    admin_text = (
        f"<b>{_t(lang, 'complaint_new')}</b>\n\n"
        f"{_t(lang, 'from_user')}: {safe_name}\n"
        f"Username: @{safe_username}\n"
        f"TG ID: <code>{user.tg_id}</code>\n"
        f"{_t(lang, 'target')}: <code>{safe_target}</code>\n"
        f"{_t(lang, 'text')}: {safe_body}\n\n"
        f"#complaint_{entry.id if entry else 'new'}"
    )
    await _notify_targets(bot, 'complaints', admin_text)
    await state.clear()
    await message.answer(_t(lang, 'complaint_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))
