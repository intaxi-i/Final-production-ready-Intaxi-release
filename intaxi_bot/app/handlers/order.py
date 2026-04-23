from __future__ import annotations

from aiogram import F, Bot, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.database.requests as rq
import app.keyboards as kb
from app.keyboards import mini_app_web_app
from app.miniapp_routes import city_create_url, city_main_url, city_my_orders_url, city_offers_url, current_trip_url, intercity_main_url, intercity_my_requests_url, intercity_my_routes_url, intercity_offers_url, intercity_request_url, intercity_route_url
from app.strings import MESSAGES
from app.database.models import async_session, IntercityRouteV1, IntercityRequestV1
from sqlalchemy import select

router = Router()


def _lang_pack(lang: str) -> dict:
    return {
        'ru': {
            'no_active_trip': 'У вас сейчас нет активного заказа или маршрута.',
            'city_trip_title': 'Текущий городской заказ',
            'intercity_route_title': 'Текущий межгород-маршрут',
            'intercity_request_title': 'Текущая межгород-заявка',
            'id': 'ID',
            'city': 'Город',
            'route': 'Маршрут',
            'from': 'Откуда',
            'to': 'Куда',
            'date': 'Дата',
            'time': 'Время',
            'seats': 'Мест',
            'price': 'Цена',
            'status': 'Статус',
            'open_city_hub': 'Открыть городской раздел в Mini App.',
            'open_intercity_hub': 'Открыть междугородний раздел в Mini App.',
            'open_city_app': 'Открыть город',
            'create_city_offer': 'Создать предложение',
            'passenger_city_orders': 'Заказы пассажиров',
            'driver_city_offers': 'Предложения водителей',
            'my_city_orders': 'Мои городские заказы',
            'open_intercity_app': 'Открыть межгород',
            'create_route': 'Создать маршрут',
            'available_requests': 'Доступные заявки',
            'my_routes': 'Мои маршруты',
            'create_request': 'Создать заявку',
            'available_routes': 'Доступные маршруты',
            'my_requests': 'Мои заявки',
            'open_current_trip': 'Открыть текущую поездку',
            'open_map': 'Открыть карту',
            'closed': 'Закрыто.',
            'open_miniapp_continue': 'Открой Mini App для продолжения сценария.',
            'open_miniapp_button': '📱 Открыть Mini App',
            'not_found': 'Не найдено или нет доступа',
            'city_order_closed': 'Городской заказ #{id} закрыт.',
            'route_closed': 'Маршрут #{id} снят.',
            'request_closed': 'Межгород-заявка #{id} закрыта.',
            'complaint_prompt': 'Напиши жалобу одним сообщением. Она будет отправлена администраторам.',
            'complaint_new': 'Новая жалоба',
            'from_user': 'От',
            'target': 'Цель',
            'text': 'Текст',
            'complaint_sent': '✅ Жалоба отправлена.',
            'fallback': 'Этот сценарий в текущей сборке переведён в Mini App или ещё не восстановлен полностью. Кнопка перехвачена, чтобы не было not handled.',
            'home_emoji': '🏠',
        },
        'uz': {
            'no_active_trip': 'Hozir sizda faol buyurtma yoki yo‘nalish yo‘q.',
            'city_trip_title': 'Joriy shahar buyurtmasi',
            'intercity_route_title': 'Joriy shaharlararo yo‘nalish',
            'intercity_request_title': 'Joriy shaharlararo so‘rov',
            'id': 'ID',
            'city': 'Shahar',
            'route': 'Yo‘nalish',
            'from': 'Qayerdan',
            'to': 'Qayerga',
            'date': 'Sana',
            'time': 'Vaqt',
            'seats': 'Joylar',
            'price': 'Narx',
            'status': 'Holat',
            'open_city_hub': 'Mini App ichida shahar bo‘limini oching.',
            'open_intercity_hub': 'Mini App ichida shaharlararo bo‘limni oching.',
            'open_city_app': 'Shaharni ochish',
            'create_city_offer': 'Taklif yaratish',
            'passenger_city_orders': 'Yo‘lovchi buyurtmalari',
            'driver_city_offers': 'Haydovchi takliflari',
            'my_city_orders': 'Mening shahar buyurtmalarim',
            'open_intercity_app': 'Shaharlararoni ochish',
            'create_route': 'Yo‘nalish yaratish',
            'available_requests': 'Mavjud so‘rovlar',
            'my_routes': 'Mening yo‘nalishlarim',
            'create_request': 'So‘rov yaratish',
            'available_routes': 'Mavjud yo‘nalishlar',
            'my_requests': 'Mening so‘rovlarim',
            'open_current_trip': 'Joriy safarni ochish',
            'open_map': 'Xaritani ochish',
            'closed': 'Yopildi.',
            'open_miniapp_continue': 'Davom etish uchun Mini Appni oching.',
            'open_miniapp_button': '📱 Mini Appni ochish',
            'not_found': 'Topilmadi yoki ruxsat yo‘q',
            'city_order_closed': 'Shahar buyurtmasi #{id} yopildi.',
            'route_closed': 'Yo‘nalish #{id} yopildi.',
            'request_closed': 'Shaharlararo so‘rov #{id} yopildi.',
            'complaint_prompt': 'Shikoyatni bitta xabar bilan yozing. U administratorlarga yuboriladi.',
            'complaint_new': 'Yangi shikoyat',
            'from_user': 'Kimdan',
            'target': 'Maqsad',
            'text': 'Matn',
            'complaint_sent': '✅ Shikoyat yuborildi.',
            'fallback': 'Bu ssenariy joriy buildda Mini Appga o‘tkazilgan yoki hali to‘liq tiklanmagan. Tugma ushlab qolindi, not handled bo‘lmasligi uchun.',
            'home_emoji': '🏠',
        },
        'en': {
            'no_active_trip': 'You do not have an active order or route right now.',
            'city_trip_title': 'Current city order',
            'intercity_route_title': 'Current intercity route',
            'intercity_request_title': 'Current intercity request',
            'id': 'ID',
            'city': 'City',
            'route': 'Route',
            'from': 'From',
            'to': 'To',
            'date': 'Date',
            'time': 'Time',
            'seats': 'Seats',
            'price': 'Price',
            'status': 'Status',
            'open_city_hub': 'Open the city section in the Mini App.',
            'open_intercity_hub': 'Open the intercity section in the Mini App.',
            'open_city_app': 'Open city',
            'create_city_offer': 'Create offer',
            'passenger_city_orders': 'Passenger orders',
            'driver_city_offers': 'Driver offers',
            'my_city_orders': 'My city orders',
            'open_intercity_app': 'Open intercity',
            'create_route': 'Create route',
            'available_requests': 'Available requests',
            'my_routes': 'My routes',
            'create_request': 'Create request',
            'available_routes': 'Available routes',
            'my_requests': 'My requests',
            'open_current_trip': 'Open current trip',
            'open_map': 'Open map',
            'closed': 'Closed.',
            'open_miniapp_continue': 'Open the Mini App to continue.',
            'open_miniapp_button': '📱 Open Mini App',
            'not_found': 'Not found or access denied',
            'city_order_closed': 'City order #{id} has been closed.',
            'route_closed': 'Route #{id} has been closed.',
            'request_closed': 'Intercity request #{id} has been closed.',
            'complaint_prompt': 'Send your complaint in one message. It will be forwarded to the admins.',
            'complaint_new': 'New complaint',
            'from_user': 'From',
            'target': 'Target',
            'text': 'Text',
            'complaint_sent': '✅ Complaint sent.',
            'fallback': 'This scenario has been moved to the Mini App in the current build or is not fully restored yet. The button was intercepted to avoid not handled.',
            'home_emoji': '🏠',
        },
        'ar': {
            'no_active_trip': 'ليس لديك الآن طلب أو مسار نشط.',
            'city_trip_title': 'الطلب الحالي داخل المدينة',
            'intercity_route_title': 'المسار الحالي بين المدن',
            'intercity_request_title': 'الطلب الحالي بين المدن',
            'id': 'ID',
            'city': 'المدينة',
            'route': 'المسار',
            'from': 'من',
            'to': 'إلى',
            'date': 'التاريخ',
            'time': 'الوقت',
            'seats': 'المقاعد',
            'price': 'السعر',
            'status': 'الحالة',
            'open_city_hub': 'افتح قسم المدينة داخل Mini App.',
            'open_intercity_hub': 'افتح قسم بين المدن داخل Mini App.',
            'open_city_app': 'فتح المدينة',
            'create_city_offer': 'إنشاء عرض',
            'passenger_city_orders': 'طلبات الركاب',
            'driver_city_offers': 'عروض السائقين',
            'my_city_orders': 'طلباتي داخل المدينة',
            'open_intercity_app': 'فتح بين المدن',
            'create_route': 'إنشاء مسار',
            'available_requests': 'الطلبات المتاحة',
            'my_routes': 'مساراتي',
            'create_request': 'إنشاء طلب',
            'available_routes': 'المسارات المتاحة',
            'my_requests': 'طلباتي',
            'open_current_trip': 'فتح الرحلة الحالية',
            'open_map': 'فتح الخريطة',
            'closed': 'تم الإغلاق.',
            'open_miniapp_continue': 'افتح Mini App للمتابعة.',
            'open_miniapp_button': '📱 فتح Mini App',
            'not_found': 'غير موجود أو لا توجد صلاحية',
            'city_order_closed': 'تم إغلاق طلب المدينة #{id}.',
            'route_closed': 'تم إغلاق المسار #{id}.',
            'request_closed': 'تم إغلاق طلب بين المدن #{id}.',
            'complaint_prompt': 'اكتب الشكوى في رسالة واحدة. سيتم إرسالها إلى المشرفين.',
            'complaint_new': 'شكوى جديدة',
            'from_user': 'من',
            'target': 'الهدف',
            'text': 'النص',
            'complaint_sent': '✅ تم إرسال الشكوى.',
            'fallback': 'تم نقل هذا السيناريو إلى Mini App في هذه النسخة أو لم تتم استعادته بالكامل بعد. تم اعتراض الزر حتى لا يظهر not handled.',
            'home_emoji': '🏠',
        },
    }.get(lang, {
        'no_active_trip': 'У вас сейчас нет активного заказа или маршрута.',
        'city_trip_title': 'Текущий городской заказ',
        'intercity_route_title': 'Текущий межгород-маршрут',
        'intercity_request_title': 'Текущая межгород-заявка',
        'id': 'ID',
        'city': 'Город',
        'route': 'Маршрут',
        'from': 'Откуда',
        'to': 'Куда',
        'date': 'Дата',
        'time': 'Время',
        'seats': 'Мест',
        'price': 'Цена',
        'status': 'Статус',
        'open_city_hub': 'Открыть городской раздел в Mini App.',
        'open_intercity_hub': 'Открыть междугородний раздел в Mini App.',
        'open_city_app': 'Открыть город',
        'create_city_offer': 'Создать предложение',
        'passenger_city_orders': 'Заказы пассажиров',
        'driver_city_offers': 'Предложения водителей',
        'my_city_orders': 'Мои городские заказы',
        'open_intercity_app': 'Открыть межгород',
        'create_route': 'Создать маршрут',
        'available_requests': 'Доступные заявки',
        'my_routes': 'Мои маршруты',
        'create_request': 'Создать заявку',
        'available_routes': 'Доступные маршруты',
        'my_requests': 'Мои заявки',
        'open_current_trip': 'Открыть текущую поездку',
        'open_map': 'Открыть карту',
        'closed': 'Закрыто.',
        'open_miniapp_continue': 'Открой Mini App для продолжения сценария.',
        'open_miniapp_button': '📱 Открыть Mini App',
        'not_found': 'Не найдено или нет доступа',
        'city_order_closed': 'Городской заказ #{id} закрыт.',
        'route_closed': 'Маршрут #{id} снят.',
        'request_closed': 'Межгород-заявка #{id} закрыта.',
        'complaint_prompt': 'Напиши жалобу одним сообщением. Она будет отправлена администраторам.',
        'complaint_new': 'Новая жалоба',
        'from_user': 'От',
        'target': 'Цель',
        'text': 'Текст',
        'complaint_sent': '✅ Жалоба отправлена.',
        'fallback': 'Этот сценарий в текущей сборке переведён в Mini App или ещё не восстановлен полностью. Кнопка перехвачена, чтобы не было not handled.',
        'home_emoji': '🏠',
    })



def _matches(values: list[str]):
    def inner(message: types.Message) -> bool:
        return (message.text or '') in values
    return inner


CITY_TEXTS = [v.get('btn_fast_order') for v in MESSAGES.values() if v.get('btn_fast_order')]
INTERCITY_TEXTS = []
CURRENT_ORDER_TEXTS = []
for lang in MESSAGES.values():
    for key in ('btn_intercity_passenger', 'btn_intercity_driver'):
        if lang.get(key) and lang.get(key) not in INTERCITY_TEXTS:
            INTERCITY_TEXTS.append(lang.get(key))
for data in kb.LOCAL_DEFAULTS.values():
    if data.get('btn_current_order') and data['btn_current_order'] not in CURRENT_ORDER_TEXTS:
        CURRENT_ORDER_TEXTS.append(data['btn_current_order'])


def _legacy_recovery_markup(lang: str, callback_data: str):
    builder = InlineKeyboardBuilder()
    current_text = _lang_pack(lang)['current_trip']
    if callback_data.startswith(('ic', 'int', 'route', 'intercity_')) or 'intercity' in callback_data:
        builder.button(text=current_text, web_app=types.WebAppInfo(url=current_trip_url()))
        builder.button(text=_lang_pack(lang)['open_intercity_app'], web_app=types.WebAppInfo(url=intercity_main_url()))
    else:
        builder.button(text=current_text, web_app=types.WebAppInfo(url=current_trip_url()))
        builder.button(text=_lang_pack(lang)['open_city_app'], web_app=types.WebAppInfo(url=city_main_url()))
    builder.adjust(1)
    return builder.as_markup()


UNSUPPORTED_INLINE_PREFIXES = (
    'acc_', 'acceptoffer_', 'arrived_', 'cancelsearch_', 'coming_', 'drv_offer_price_',
    'finish_', 'icarrived_', 'iccoming_', 'icdetail_', 'icfinish_', 'icreqprice_',
    'icreqtime_', 'icroffer_', 'icrsel_', 'icstart_', 'idreqacc_', 'idreqrej_',
    'intacc_', 'passdestnote_', 'passpicknote_', 'passprice_', 'passstop_', 'passtime_',
    'payintercity_', 'payorder_', 'rate_', 'rejectoffer_', 'routeprice_', 'routetime_',
    'intercity_common_cancel',
)


class ComplaintFlow(StatesGroup):
    waiting_text = State()


async def _notify_targets(bot: Bot, permission: str, text: str, *, parse_mode: str | None = 'HTML') -> None:
    for admin_id in await rq.get_admin_targets_by_permission(permission):
        try:
            await bot.send_message(admin_id, text, parse_mode=parse_mode, disable_web_page_preview=True)
        except Exception:
            pass


def _trip_summary(item, lang: str = 'ru') -> tuple[str, str | None]:
    p = _lang_pack(lang)

    if not item:
        return p['no_active_trip'], None

    if hasattr(item, 'from_address'):
        text = (
            f"<b>{p['city_trip_title']}</b>\n\n"
            f"{p['id']}: <code>{item.id}</code>\n"
            f"{p['city']}: {item.city or '—'}\n"
            f"{p['from']}: {item.from_address or '—'}\n"
            f"{p['to']}: {item.to_address or '—'}\n"
            f"{p['seats']}: {item.seats or 1}\n"
            f"{p['price']}: {item.price or 0}\n"
            f"{p['status']}: {item.status or 'active'}"
        )
        return text, getattr(item, 'from_address', None)

    if hasattr(item, 'departure_date'):
        text = (
            f"<b>{p['intercity_route_title']}</b>\n\n"
            f"{p['id']}: <code>{item.id}</code>\n"
            f"{p['route']}: {item.from_city or '—'} → {item.to_city or '—'}\n"
            f"{p['date']}: {item.departure_date or '—'}\n"
            f"{p['time']}: {item.departure_time or '—'}\n"
            f"{p['seats']}: {item.seats or 1}\n"
            f"{p['price']}: {item.price or 0}\n"
            f"{p['status']}: {item.status or 'active'}"
        )
        return text, f"{item.from_city or ''}, {item.to_city or ''}".strip(', ')

    text = (
        f"<b>{p['intercity_request_title']}</b>\n\n"
        f"{p['id']}: <code>{item.id}</code>\n"
        f"{p['route']}: {item.from_city or '—'} → {item.to_city or '—'}\n"
        f"{p['date']}: {getattr(item, 'desired_date', None) or '—'}\n"
        f"{p['time']}: {getattr(item, 'desired_time', None) or '—'}\n"
        f"{p['seats']}: {getattr(item, 'seats_needed', None) or 1}\n"
        f"{p['price']}: {getattr(item, 'price_offer', None) or 0}\n"
        f"{p['status']}: {item.status or 'active'}"
    )
    return text, f"{item.from_city or ''}, {item.to_city or ''}".strip(', ')


@router.message(_matches(CITY_TEXTS))
async def open_city_hub(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    p = _lang_pack(lang)
    is_driver_mode = bool(user.is_verified and (user.active_role or 'driver') != 'passenger')

    builder = InlineKeyboardBuilder()
    if is_driver_mode:
        builder.button(text='📝 ' + p['create_city_offer'], callback_data='citybot_create_driver')
        builder.button(text='📋 ' + p['passenger_city_orders'], callback_data='citybot_list_passenger')
    else:
        builder.button(text='📝 ' + MESSAGES.get(lang, MESSAGES['ru']).get('btn_fast_order', 'Fast order'), callback_data='citybot_create_passenger')
        builder.button(text='📋 ' + p['driver_city_offers'], callback_data='citybot_list_driver')
    builder.button(text='🗂 ' + p['my_city_orders'], callback_data='citybot_my')
    builder.button(text='📱 ' + p['open_city_app'], web_app=types.WebAppInfo(url=city_main_url('driver' if is_driver_mode else 'passenger')))

    await message.answer(p['open_city_hub'], reply_markup=builder.adjust(1).as_markup())


@router.message(_matches(INTERCITY_TEXTS))
async def open_intercity_hub(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    p = _lang_pack(lang)
    is_driver_mode = bool(user.is_verified and (user.active_role or 'driver') != 'passenger')

    builder = InlineKeyboardBuilder()
    if is_driver_mode:
        builder.button(text='📝 ' + p['create_route'], callback_data='interbot_create_route')
        builder.button(text='📋 ' + p['available_requests'], callback_data='interbot_list_requests')
        builder.button(text='🗂 ' + p['my_routes'], callback_data='interbot_my_routes')
    else:
        builder.button(text='📝 ' + p['create_request'], callback_data='interbot_create_request')
        builder.button(text='📋 ' + p['available_routes'], callback_data='interbot_list_routes')
        builder.button(text='🗂 ' + p['my_requests'], callback_data='interbot_my_requests')
    builder.button(text='📱 ' + p['open_intercity_app'], web_app=types.WebAppInfo(url=intercity_main_url('driver' if is_driver_mode else 'passenger')))

    await message.answer(p['open_intercity_hub'], reply_markup=builder.adjust(1).as_markup())


@router.message(_matches(CURRENT_ORDER_TEXTS))
async def show_current_order(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    p = _lang_pack(lang)
    item = await rq.get_current_trip_for_user(user.tg_id)
    text, map_source = _trip_summary(item, lang)
    map_link = rq.get_map_link(map_source)

    builder = InlineKeyboardBuilder()
    has_buttons = False
    if item:
        builder.button(text=p['open_current_trip'], web_app=types.WebAppInfo(url=current_trip_url()))
        has_buttons = True
    if map_link and item:
        builder.button(text=p['open_map'], url=map_link)
        has_buttons = True

    markup = builder.adjust(1).as_markup() if has_buttons else None
    await message.answer(text, reply_markup=markup, parse_mode='HTML', disable_web_page_preview=True)


@router.callback_query(F.data == 'interhub_cancel')
async def close_intercity_hub(callback: types.CallbackQuery):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    p = _lang_pack(lang)
    await callback.message.edit_text(p['closed'])
    is_admin = await rq.is_admin_user(user.tg_id)
    await callback.message.answer('🏠', reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=(not is_admin), is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger'), is_admin=is_admin))
    await callback.answer()


@router.callback_query(F.data.in_({'interhub_create_driver', 'interhub_create_passenger', 'interhub_available_driver', 'interhub_available_passenger'}))
async def open_intercity_miniapp(callback: types.CallbackQuery):
    mapping = {
        'interhub_create_driver': '/intercity/route',
        'interhub_create_passenger': '/intercity/request',
        'interhub_available_driver': '/intercity/offers',
        'interhub_available_passenger': '/intercity/offers',
    }
    target = mapping[callback.data]
    lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
    p = _lang_pack(lang)
    builder = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=p['open_miniapp_button'], web_app=mini_app_web_app(target))]])
    await callback.message.answer(p['open_miniapp_continue'], reply_markup=builder)
    await callback.answer()


@router.callback_query(F.data.startswith('cancl_'))
async def close_city_order(callback: types.CallbackQuery):
    order_id = int(callback.data.rsplit('_', 1)[1])
    row = await rq.close_city_order_for_user(order_id, callback.from_user.id)
    if not row:
        lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
        await callback.answer(_lang_pack(lang)['not_found'], show_alert=True)
        return
    lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
    await callback.message.answer(_lang_pack(lang)['city_order_closed'].format(id=order_id))
    await callback.answer('OK')


@router.callback_query(F.data.startswith('routeoff_'))
async def close_intercity_route(callback: types.CallbackQuery):
    route_id = int(callback.data.rsplit('_', 1)[1])
    row = await rq.close_intercity_route_for_user(route_id, callback.from_user.id)
    if not row:
        lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
        await callback.answer(_lang_pack(lang)['not_found'], show_alert=True)
        return
    lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
    await callback.message.answer(_lang_pack(lang)['route_closed'].format(id=route_id))
    await callback.answer('OK')


@router.callback_query(F.data.startswith('icreqcancel_'))
async def close_intercity_request(callback: types.CallbackQuery):
    request_id = int(callback.data.rsplit('_', 1)[1])
    row = await rq.close_intercity_request_for_user(request_id, callback.from_user.id)
    if not row:
        lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
        await callback.answer(_lang_pack(lang)['not_found'], show_alert=True)
        return
    lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
    await callback.message.answer(_lang_pack(lang)['request_closed'].format(id=request_id))
    await callback.answer('OK')


@router.callback_query(F.data.startswith(('compl_city_driver_', 'compl_city_passenger_', 'compl_intercity_driver_', 'compl_intercity_passenger_')))
async def complaint_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ComplaintFlow.waiting_text)
    await state.update_data(complaint_target=callback.data)
    lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
    await callback.message.answer(_lang_pack(lang)['complaint_prompt'])
    await callback.answer()


@router.message(ComplaintFlow.waiting_text)
async def complaint_finish(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    target = data.get('complaint_target', '-')
    body = (message.text or '').strip()
    entry = await rq.create_feedback_entry(user.tg_id, 'complaint', 'text', text_value=body)
    p = _lang_pack(lang)
    admin_text = (
        f"<b>{p['complaint_new']}</b>\n\n"
        f"{p['from_user']}: {user.full_name or '—'}\n"
        f"Username: @{user.username or '—'}\n"
        f"TG ID: <code>{user.tg_id}</code>\n"
        f"{p['target']}: <code>{target}</code>\n"
        f"{p['text']}: {message.html_text or body}\n\n"
        f"#complaint_{entry.id if entry else 'new'}"
    )
    await _notify_targets(bot, 'complaints', admin_text)
    await state.clear()
    await message.answer(_lang_pack(lang)['complaint_sent'], reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))




class CityBotCreateFlow(StatesGroup):
    country = State()
    city = State()
    from_point = State()
    to_point = State()
    seats = State()
    price = State()
    comment = State()


class IntercityBotCreateFlow(StatesGroup):
    country = State()
    from_city = State()
    to_city = State()
    pickup_mode = State()
    date = State()
    time = State()
    seats = State()
    price = State()
    comment = State()


_FLOW_TEXTS = {
    'ru': {
        'share_location': '📍 Отправить текущую локацию',
        'send_from': 'Укажите точку отправления текстом или одним нажатием отправьте геолокацию.',
        'send_to': 'Укажите точку назначения текстом или одним нажатием отправьте геолокацию.',
        'enter_seats': 'Сколько мест нужно?',
        'enter_price': 'Укажите цену. Можно отправить 0, чтобы использовать рекомендованную цену.',
        'enter_comment': 'Добавьте комментарий или нажмите «Пропустить».',
        'skip': '⏭ Пропустить',
        'created_ok': '✅ Заказ создан и активирован.',
        'created_route_ok': '✅ Маршрут создан и опубликован.',
        'created_request_ok': '✅ Заявка создана и опубликована.',
        'operation_failed': '❌ Не удалось выполнить действие.',
        'need_number': 'Пожалуйста, отправьте число.',
        'select_country': 'Выберите страну.',
        'select_city': 'Выберите город или отправьте его текстом.',
        'select_from_city': 'Выберите город отправления или отправьте его текстом.',
        'select_to_city': 'Выберите город назначения или отправьте его текстом.',
        'enter_date': 'Укажите дату в формате YYYY-MM-DD.',
        'enter_time': 'Укажите время в формате HH:MM.',
        'pickup_mode': 'Выберите формат посадки.',
        'pickup_driver_location': 'Встреча у водителя',
        'pickup_driver_pickup': 'Водитель заберёт пассажира',
        'pickup_ask_driver': 'Уточнить у водителя',
        'market_empty': 'Сейчас активных предложений не найдено.',
        'my_empty': 'У вас пока нет активных записей.',
        'accept': '✅ Принять',
        'close': '🛑 Закрыть',
        'current_trip': '📌 Текущая поездка',
        'use_recommended': 'Использовать рекомендованную цену',
        'recommended_price': 'Рекомендованная цена за весь путь',
        'distance': 'Расстояние',
        'point_saved': 'Точка сохранена',
        'location_detected': 'Определено по локации',
        'city_menu': 'Город: доступно создание, просмотр и принятие заказов прямо в боте.',
        'intercity_menu': 'Межгород: доступно создание, просмотр и принятие маршрутов прямо в боте.',
    },
    'uz': {
        'share_location': '📍 Joriy lokatsiyani yuborish', 'send_from': 'Jo‘nash nuqtasini matn bilan yuboring yoki lokatsiya jo‘nating.', 'send_to': 'Borish nuqtasini matn bilan yuboring yoki lokatsiya jo‘nating.', 'enter_seats': 'Nechta joy kerak?', 'enter_price': 'Narxni kiriting. Tavsiya narxidan foydalanish uchun 0 yuboring.', 'enter_comment': 'Izoh kiriting yoki “O‘tkazib yuborish”ni bosing.', 'skip': '⏭ O‘tkazib yuborish', 'created_ok': '✅ Buyurtma yaratildi.', 'created_route_ok': '✅ Yo‘nalish yaratildi.', 'created_request_ok': '✅ So‘rov yaratildi.', 'operation_failed': '❌ Amalni bajarib bo‘lmadi.', 'need_number': 'Iltimos, raqam yuboring.', 'select_country': 'Davlatni tanlang.', 'select_city': 'Shaharni tanlang yoki matn bilan yuboring.', 'select_from_city': 'Jo‘nash shahrini tanlang yoki matn bilan yuboring.', 'select_to_city': 'Borish shahrini tanlang yoki matn bilan yuboring.', 'enter_date': 'Sanani YYYY-MM-DD formatida kiriting.', 'enter_time': 'Vaqtni HH:MM formatida kiriting.', 'pickup_mode': 'Yo‘lovchini olish usulini tanlang.', 'pickup_driver_location': 'Haydovchi joyida uchrashuv', 'pickup_driver_pickup': 'Haydovchi yo‘lovchini olib ketadi', 'pickup_ask_driver': 'Haydovchi bilan aniqlash', 'market_empty': 'Hozir faol takliflar yo‘q.', 'my_empty': 'Sizda hozircha faol yozuvlar yo‘q.', 'accept': '✅ Qabul qilish', 'close': '🛑 Yopish', 'current_trip': '📌 Joriy safar', 'use_recommended': 'Tavsiya narxidan foydalanish', 'recommended_price': 'Butun yo‘l uchun tavsiya narx', 'distance': 'Masofa', 'point_saved': 'Nuqta saqlandi', 'location_detected': 'Lokatsiya bo‘yicha aniqlandi', 'city_menu': 'Shahar: buyurtmani bot ichida yaratish, ko‘rish va qabul qilish mumkin.', 'intercity_menu': 'Shaharlararo: yo‘nalishlarni bot ichida yaratish, ko‘rish va qabul qilish mumkin.'
    },
    'en': {
        'share_location': '📍 Send current location', 'send_from': 'Send the pickup point as text or share your location in one tap.', 'send_to': 'Send the destination as text or share your location in one tap.', 'enter_seats': 'How many seats are needed?', 'enter_price': 'Enter the price. Send 0 to use the recommended price.', 'enter_comment': 'Add a comment or press Skip.', 'skip': '⏭ Skip', 'created_ok': '✅ Order created.', 'created_route_ok': '✅ Route created.', 'created_request_ok': '✅ Request created.', 'operation_failed': '❌ Operation failed.', 'need_number': 'Please send a number.', 'select_country': 'Choose a country.', 'select_city': 'Choose a city or send it as text.', 'select_from_city': 'Choose the departure city or send it as text.', 'select_to_city': 'Choose the destination city or send it as text.', 'enter_date': 'Enter the date in YYYY-MM-DD format.', 'enter_time': 'Enter the time in HH:MM format.', 'pickup_mode': 'Choose the pickup mode.', 'pickup_driver_location': 'Meet at driver location', 'pickup_driver_pickup': 'Driver will pick the passenger up', 'pickup_ask_driver': 'Clarify with driver', 'market_empty': 'No active offers right now.', 'my_empty': 'You have no active items yet.', 'accept': '✅ Accept', 'close': '🛑 Close', 'current_trip': '📌 Current trip', 'use_recommended': 'Use recommended price', 'recommended_price': 'Recommended total price', 'distance': 'Distance', 'point_saved': 'Point saved', 'location_detected': 'Detected from location', 'city_menu': 'City mode is fully available in the bot now.', 'intercity_menu': 'Intercity mode is fully available in the bot now.'
    },
    'ar': {
        'share_location': '📍 إرسال الموقع الحالي', 'send_from': 'أرسل نقطة الانطلاق نصًا أو أرسل موقعك بضغطة واحدة.', 'send_to': 'أرسل نقطة الوصول نصًا أو أرسل موقعك بضغطة واحدة.', 'enter_seats': 'كم عدد المقاعد المطلوبة؟', 'enter_price': 'أدخل السعر. أرسل 0 لاستخدام السعر المقترح.', 'enter_comment': 'أضف تعليقًا أو اضغط تخطٍ.', 'skip': '⏭ تخطي', 'created_ok': '✅ تم إنشاء الطلب.', 'created_route_ok': '✅ تم إنشاء المسار.', 'created_request_ok': '✅ تم إنشاء الطلب بين المدن.', 'operation_failed': '❌ تعذر تنفيذ العملية.', 'need_number': 'الرجاء إرسال رقم.', 'select_country': 'اختر الدولة.', 'select_city': 'اختر المدينة أو أرسلها نصًا.', 'select_from_city': 'اختر مدينة الانطلاق أو أرسلها نصًا.', 'select_to_city': 'اختر مدينة الوصول أو أرسلها نصًا.', 'enter_date': 'أدخل التاريخ بصيغة YYYY-MM-DD.', 'enter_time': 'أدخل الوقت بصيغة HH:MM.', 'pickup_mode': 'اختر طريقة الالتقاء.', 'pickup_driver_location': 'الالتقاء عند السائق', 'pickup_driver_pickup': 'السائق سيصطحب الراكب', 'pickup_ask_driver': 'التأكيد مع السائق', 'market_empty': 'لا توجد عروض نشطة الآن.', 'my_empty': 'ليس لديك عناصر نشطة بعد.', 'accept': '✅ قبول', 'close': '🛑 إغلاق', 'current_trip': '📌 الرحلة الحالية', 'use_recommended': 'استخدام السعر المقترح', 'recommended_price': 'السعر المقترح لكامل الطريق', 'distance': 'المسافة', 'point_saved': 'تم حفظ النقطة', 'location_detected': 'تم التحديد من الموقع', 'city_menu': 'قسم المدينة يعمل الآن داخل البوت.', 'intercity_menu': 'قسم بين المدن يعمل الآن داخل البوت.'
    },
}


def _ft(lang: str, key: str) -> str:
    return _FLOW_TEXTS.get(lang, _FLOW_TEXTS['ru']).get(key, _FLOW_TEXTS['ru'].get(key, key))


def _remove_reply() -> types.ReplyKeyboardRemove:
    return types.ReplyKeyboardRemove()


def _cancel_reply(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_cancel', '❌ Cancel'))]], resize_keyboard=True, one_time_keyboard=True)


def _skip_or_cancel_reply(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text=_ft(lang, 'skip'))], [types.KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_cancel', '❌ Cancel'))]], resize_keyboard=True, one_time_keyboard=True)


def _location_reply(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text=_ft(lang, 'share_location'), request_location=True)], [types.KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_cancel', '❌ Cancel'))]], resize_keyboard=True, one_time_keyboard=True)


def _country_keyboard(prefix: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in ('uz', 'tr', 'sa'):
        builder.button(text=code.upper(), callback_data=f'{prefix}{code}')
    return builder.adjust(3).as_markup()


def _city_keyboard(lang: str, country: str, prefix: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for city in MESSAGES.get(lang, MESSAGES['ru']).get('cities', {}).get(country, []):
        builder.button(text=city, callback_data=f'{prefix}{city}')
    return builder.adjust(2).as_markup()


def _pickup_mode_keyboard(lang: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_ft(lang, 'pickup_driver_location'), callback_data='interflow_pickup_driver_location')
    builder.button(text=_ft(lang, 'pickup_driver_pickup'), callback_data='interflow_pickup_driver_pickup')
    builder.button(text=_ft(lang, 'pickup_ask_driver'), callback_data='interflow_pickup_ask_driver')
    return builder.adjust(1).as_markup()


async def _reverse_geocode(lat: float, lng: float) -> dict[str, str | float] | None:
    try:
        import json as _json
        from urllib.request import Request, urlopen
        url = f'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}&zoom=18&addressdetails=1'
        req = Request(url, headers={'User-Agent': 'INTAXI/1.0'})
        with urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read().decode('utf-8'))
        address = data.get('display_name') or f'{lat:.6f}, {lng:.6f}'
        address_info = data.get('address') or {}
        city = address_info.get('city') or address_info.get('town') or address_info.get('village') or address_info.get('state') or ''
        country_name = (address_info.get('country_code') or '').lower()
        return {'address': address, 'city': city, 'country': country_name, 'lat': lat, 'lng': lng}
    except Exception:
        return None


def _country_from_name(value: str | None) -> str | None:
    mapping = {'uz': 'uz', 'uzbekistan': 'uz', 'o‘zbekiston': 'uz', 'узбекистан': 'uz', 'tr': 'tr', 'turkey': 'tr', 'turkiye': 'tr', 'türkiye': 'tr', 'турция': 'tr', 'sa': 'sa', 'saudi': 'sa', 'saudi arabia': 'sa', 'саудовская аравия': 'sa'}
    if not value:
        return None
    return mapping.get(value.strip().lower())


def _country_label(lang: str, code: str) -> str:
    return MESSAGES.get(lang, MESSAGES['ru']).get('countries', {}).get(code, code.upper())


def _estimate_total_price(country: str, from_lat: float | None, from_lng: float | None, to_lat: float | None, to_lng: float | None) -> tuple[float | None, float | None, str]:
    currency, per_km = rq.DEFAULT_TARIFFS.get((country or 'uz').lower(), ('USD', 0.0))
    if None in {from_lat, from_lng, to_lat, to_lng}:
        return None, None, currency
    distance = round(rq.haversine_km(float(from_lat), float(from_lng), float(to_lat), float(to_lng)), 2)
    return round(distance * float(per_km), 2), distance, currency


async def _show_city_market(callback: types.CallbackQuery, wanted_role: str):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    items = await rq.list_city_market_for_user(user.tg_id, wanted_role=wanted_role, limit=10)
    if not items:
        await callback.message.answer(_ft(lang, 'market_empty'))
        await callback.answer()
        return
    for entry in items:
        row = entry['order']
        runtime = entry['runtime']
        creator = entry['creator']
        vehicle = entry['vehicle']
        text = (f"<b>{row.city}</b>\n"
                f"#{row.id} · {row.from_address or '—'}"
                f"{(' → ' + row.to_address) if row.to_address else ''}\n"
                f"{_lang_pack(lang)['price']}: {row.price}\n"
                f"{_ft(lang, 'distance')}: {getattr(runtime, 'estimated_distance_km', None) or '—'} km")
        if creator:
            text += f"\n{_lang_pack(lang)['from_user']}: {creator.full_name or creator.tg_id}"
        if vehicle:
            text += f"\n🚗 {vehicle.brand or ''} {vehicle.model or ''} {vehicle.plate or ''}".strip()
        builder = InlineKeyboardBuilder()
        builder.button(text=_ft(lang, 'accept'), callback_data=f'citybot_accept_{row.id}')
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


async def _show_my_city_orders(callback: types.CallbackQuery):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    items = await rq.list_user_city_orders(user.tg_id, limit=10)
    if not items:
        await callback.message.answer(_ft(lang, 'my_empty'))
        await callback.answer()
        return
    for entry in items:
        row = entry['order']
        runtime = entry['runtime']
        text = (f"<b>{row.city}</b>\n#{row.id} · {row.from_address or '—'}{(' → ' + row.to_address) if row.to_address else ''}\n"
                f"{_lang_pack(lang)['status']}: {row.status}\n{_lang_pack(lang)['price']}: {row.price}")
        builder = InlineKeyboardBuilder()
        if runtime and getattr(runtime, 'active_trip_id', None):
            builder.button(text=_ft(lang, 'current_trip'), web_app=types.WebAppInfo(url=current_trip_url()))
        if row.status not in {'closed', 'completed', 'cancelled'} and not (runtime and getattr(runtime, 'active_trip_id', None)):
            builder.button(text=_ft(lang, 'close'), callback_data=f'cancl_{row.id}')
        await callback.message.answer(text, reply_markup=builder.adjust(1).as_markup(), parse_mode='HTML')
    await callback.answer()


async def _show_intercity_market(callback: types.CallbackQuery, kind: str):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    rows = await rq.list_intercity_market_for_user(user.tg_id, kind=kind, limit=10)
    if not rows:
        await callback.message.answer(_ft(lang, 'market_empty'))
        await callback.answer()
        return
    for row in rows:
        if kind == 'route':
            text = f"<b>{row.from_city} → {row.to_city}</b>\n#{row.id}\n{_lang_pack(lang)['date']}: {row.departure_date or '—'} · {_lang_pack(lang)['time']}: {row.departure_time or '—'}\n{_lang_pack(lang)['price']}: {row.price}"
            cb = f'interbot_accept_route_{row.id}'
        else:
            text = f"<b>{row.from_city} → {row.to_city}</b>\n#{row.id}\n{_lang_pack(lang)['date']}: {row.desired_date or '—'} · {_lang_pack(lang)['time']}: {row.desired_time or '—'}\n{_lang_pack(lang)['price']}: {row.price_offer}"
            cb = f'interbot_accept_request_{row.id}'
        builder = InlineKeyboardBuilder()
        builder.button(text=_ft(lang, 'accept'), callback_data=cb)
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


async def _show_my_intercity(callback: types.CallbackQuery, kind: str):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    async with rq.async_session() as session:
        if kind == 'route':
            own_rows = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.creator_tg_id == user.tg_id).order_by(IntercityRouteV1.id.desc()).limit(10))).all()
        else:
            own_rows = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.creator_tg_id == user.tg_id).order_by(IntercityRequestV1.id.desc()).limit(10))).all()
    if not own_rows:
        await callback.message.answer(_ft(lang, 'my_empty'))
        await callback.answer()
        return
    for row in own_rows:
        if kind == 'route':
            text = f"<b>{row.from_city} → {row.to_city}</b>\n#{row.id}\n{_lang_pack(lang)['status']}: {row.status}\n{_lang_pack(lang)['price']}: {row.price}"
            close_cb = f'routeoff_{row.id}'
        else:
            text = f"<b>{row.from_city} → {row.to_city}</b>\n#{row.id}\n{_lang_pack(lang)['status']}: {row.status}\n{_lang_pack(lang)['price']}: {row.price_offer}"
            close_cb = f'icreqcancel_{row.id}'
        builder = InlineKeyboardBuilder()
        if row.status not in {'closed', 'completed', 'cancelled'}:
            builder.button(text=_ft(lang, 'close'), callback_data=close_cb)
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'citybot_create_passenger')
async def citybot_create_passenger(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.update_data(city_role='passenger')
    await state.set_state(CityBotCreateFlow.country)
    await callback.message.answer(_ft(lang, 'select_country'), reply_markup=_country_keyboard('cityflow_country_'))
    await callback.answer()


@router.callback_query(F.data == 'citybot_create_driver')
async def citybot_create_driver(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    if not user.is_verified:
        await callback.answer(_lang_pack(lang)['not_found'], show_alert=True)
        return
    await state.clear()
    await state.update_data(city_role='driver')
    await state.set_state(CityBotCreateFlow.country)
    await callback.message.answer(_ft(lang, 'select_country'), reply_markup=_country_keyboard('cityflow_country_'))
    await callback.answer()


@router.callback_query(F.data == 'citybot_list_driver')
async def citybot_list_driver(callback: types.CallbackQuery):
    await _show_city_market(callback, 'driver')


@router.callback_query(F.data == 'citybot_list_passenger')
async def citybot_list_passenger(callback: types.CallbackQuery):
    await _show_city_market(callback, 'passenger')


@router.callback_query(F.data == 'citybot_my')
async def citybot_my(callback: types.CallbackQuery):
    await _show_my_city_orders(callback)


@router.callback_query(F.data.startswith('citybot_accept_'))
async def citybot_accept(callback: types.CallbackQuery):
    trip = await rq.accept_city_offer_for_user(int(callback.data.rsplit('_', 1)[1]), callback.from_user.id)
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    if not trip:
        await callback.answer(_ft(lang, 'operation_failed'), show_alert=True)
        return
    text, _ = _trip_summary(trip, lang)
    builder = InlineKeyboardBuilder()
    builder.button(text=_ft(lang, 'current_trip'), web_app=types.WebAppInfo(url=current_trip_url()))
    await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode='HTML')
    await callback.answer('OK')


@router.callback_query(F.data.startswith('cityflow_country_'), CityBotCreateFlow.country)
async def cityflow_country(callback: types.CallbackQuery, state: FSMContext):
    country = callback.data.split('cityflow_country_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(country=country)
    await state.set_state(CityBotCreateFlow.city)
    await callback.message.answer(f"{_ft(lang, 'select_city')}\n{_country_label(lang, country)}", reply_markup=_city_keyboard(lang, country, 'cityflow_city_'))
    await callback.answer()


@router.callback_query(F.data.startswith('cityflow_city_'), CityBotCreateFlow.city)
async def cityflow_city_callback(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('cityflow_city_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(city=city)
    await state.set_state(CityBotCreateFlow.from_point)
    await callback.message.answer(_ft(lang, 'send_from'), reply_markup=_location_reply(lang))
    await callback.answer()


@router.message(CityBotCreateFlow.city)
async def cityflow_city_text(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    city = (message.text or '').strip()
    if not city:
        await message.answer(_ft(lang, 'select_city'))
        return
    await state.update_data(city=city)
    await state.set_state(CityBotCreateFlow.from_point)
    await message.answer(_ft(lang, 'send_from'), reply_markup=_location_reply(lang))


async def _capture_point_from_message(message: types.Message, state: FSMContext, point_key: str) -> tuple[str, dict] | None:
    data = await state.get_data()
    lang = (await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)).language or 'ru'
    payload = {}
    address = ''
    if message.location:
        lat = round(message.location.latitude, 6)
        lng = round(message.location.longitude, 6)
        geo = await _reverse_geocode(lat, lng)
        address = (geo or {}).get('address') or f'{lat}, {lng}'
        payload = {f'{point_key}_lat': lat, f'{point_key}_lng': lng, f'{point_key}_address': address}
        if geo and geo.get('city') and not data.get('city'):
            payload['city'] = str(geo.get('city'))
        c = _country_from_name((geo or {}).get('country'))
        if c and not data.get('country'):
            payload['country'] = c
    else:
        address = (message.text or '').strip()
        if not address:
            await message.answer(_ft(lang, 'operation_failed'))
            return None
        payload = {f'{point_key}_address': address}
    await state.update_data(**payload)
    return address, payload


@router.message(CityBotCreateFlow.from_point)
async def cityflow_from_point(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    captured = await _capture_point_from_message(message, state, 'from')
    if not captured:
        return
    await state.set_state(CityBotCreateFlow.to_point)
    await message.answer(f"{_ft(lang, 'point_saved')}: {captured[0]}\n\n{_ft(lang, 'send_to')}", reply_markup=_location_reply(lang))


@router.message(CityBotCreateFlow.to_point)
async def cityflow_to_point(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    captured = await _capture_point_from_message(message, state, 'to')
    if not captured:
        return
    data = await state.get_data()
    await state.set_state(CityBotCreateFlow.seats)
    rec_price, distance, currency = _estimate_total_price(data.get('country', 'uz'), data.get('from_lat'), data.get('from_lng'), data.get('to_lat'), data.get('to_lng'))
    extra = ''
    if rec_price is not None:
        extra = f"\n{_ft(lang, 'distance')}: {distance} km\n{_ft(lang, 'recommended_price')}: {rec_price} {currency}"
    await message.answer(f"{_ft(lang, 'point_saved')}: {captured[0]}{extra}\n\n{_ft(lang, 'enter_seats')}", reply_markup=_cancel_reply(lang))


@router.message(CityBotCreateFlow.seats)
async def cityflow_seats(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    try:
        seats = max(1, int((message.text or '1').strip()))
    except Exception:
        await message.answer(_ft(lang, 'need_number'))
        return
    await state.update_data(seats=seats)
    await state.set_state(CityBotCreateFlow.price)
    await message.answer(_ft(lang, 'enter_price'), reply_markup=_cancel_reply(lang))


@router.message(CityBotCreateFlow.price)
async def cityflow_price(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    try:
        price = float((message.text or '0').replace(',', '.').strip())
    except Exception:
        await message.answer(_ft(lang, 'need_number'))
        return
    await state.update_data(price=price)
    await state.set_state(CityBotCreateFlow.comment)
    await message.answer(_ft(lang, 'enter_comment'), reply_markup=_skip_or_cancel_reply(lang))


@router.message(CityBotCreateFlow.comment)
async def cityflow_comment(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    comment = '' if (message.text or '').strip() == _ft(lang, 'skip') else (message.text or '').strip()
    try:
        order, runtime = await rq.create_city_order_bot(creator_tg_id=user.tg_id, role=data.get('city_role', 'passenger'), country=data.get('country', user.country or 'uz'), city=data.get('city', user.city or ''), from_address=data.get('from_address', ''), to_address=data.get('to_address', ''), seats=int(data.get('seats', 1) or 1), price=float(data.get('price', 0) or 0), comment=comment, from_lat=data.get('from_lat'), from_lng=data.get('from_lng'), to_lat=data.get('to_lat'), to_lng=data.get('to_lng'))
    except Exception as exc:
        await message.answer(f"{_ft(lang, 'operation_failed')}\n{exc}", reply_markup=_remove_reply())
        return
    await state.clear()
    text = f"{_ft(lang, 'created_ok')}\n#{order.id}\n{order.from_address} → {order.to_address}\n{_lang_pack(lang)['price']}: {order.price}"
    if getattr(runtime, 'recommended_price', None):
        text += f"\n{_ft(lang, 'recommended_price')}: {runtime.recommended_price} {runtime.currency or ''}"
    await message.answer(text, reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))


@router.callback_query(F.data == 'interbot_create_request')
async def interbot_create_request(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.update_data(inter_kind='request')
    await state.set_state(IntercityBotCreateFlow.country)
    await callback.message.answer(_ft(lang, 'select_country'), reply_markup=_country_keyboard('interflow_country_'))
    await callback.answer()


@router.callback_query(F.data == 'interbot_create_route')
async def interbot_create_route(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    if not user.is_verified:
        await callback.answer(_lang_pack(lang)['not_found'], show_alert=True)
        return
    await state.clear()
    await state.update_data(inter_kind='route')
    await state.set_state(IntercityBotCreateFlow.country)
    await callback.message.answer(_ft(lang, 'select_country'), reply_markup=_country_keyboard('interflow_country_'))
    await callback.answer()


@router.callback_query(F.data == 'interbot_list_routes')
async def interbot_list_routes(callback: types.CallbackQuery):
    await _show_intercity_market(callback, 'route')


@router.callback_query(F.data == 'interbot_list_requests')
async def interbot_list_requests(callback: types.CallbackQuery):
    await _show_intercity_market(callback, 'request')


@router.callback_query(F.data == 'interbot_my_routes')
async def interbot_my_routes(callback: types.CallbackQuery):
    await _show_my_intercity(callback, 'route')


@router.callback_query(F.data == 'interbot_my_requests')
async def interbot_my_requests(callback: types.CallbackQuery):
    await _show_my_intercity(callback, 'request')


@router.callback_query(F.data.startswith('interbot_accept_route_'))
async def interbot_accept_route(callback: types.CallbackQuery):
    row = await rq.accept_intercity_offer_for_user(kind='route', item_id=int(callback.data.rsplit('_', 1)[1]), tg_id=callback.from_user.id)
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    if not row:
        await callback.answer(_ft(lang, 'operation_failed'), show_alert=True)
        return
    await callback.message.answer(f"✅ #{row.id}: {row.from_city} → {row.to_city}\n{_lang_pack(lang)['status']}: {row.status}", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=_ft(lang, 'current_trip'), web_app=types.WebAppInfo(url=current_trip_url(trip_type='intercity_route', trip_id=row.id)))]]))
    await callback.answer('OK')


@router.callback_query(F.data.startswith('interbot_accept_request_'))
async def interbot_accept_request(callback: types.CallbackQuery):
    row = await rq.accept_intercity_offer_for_user(kind='request', item_id=int(callback.data.rsplit('_', 1)[1]), tg_id=callback.from_user.id)
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    if not row:
        await callback.answer(_ft(lang, 'operation_failed'), show_alert=True)
        return
    await callback.message.answer(f"✅ #{row.id}: {row.from_city} → {row.to_city}\n{_lang_pack(lang)['status']}: {row.status}", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=_ft(lang, 'current_trip'), web_app=types.WebAppInfo(url=current_trip_url(trip_type='intercity_request', trip_id=row.id)))]]))
    await callback.answer('OK')


@router.callback_query(F.data.startswith('interflow_country_'), IntercityBotCreateFlow.country)
async def interflow_country(callback: types.CallbackQuery, state: FSMContext):
    country = callback.data.split('interflow_country_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(country=country)
    await state.set_state(IntercityBotCreateFlow.from_city)
    await callback.message.answer(_ft(lang, 'select_from_city'), reply_markup=_city_keyboard(lang, country, 'interflow_fromcity_'))
    await callback.answer()


@router.callback_query(F.data.startswith('interflow_fromcity_'), IntercityBotCreateFlow.from_city)
async def interflow_fromcity_callback(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('interflow_fromcity_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    await state.update_data(from_city=city)
    await state.set_state(IntercityBotCreateFlow.to_city)
    await callback.message.answer(_ft(lang, 'select_to_city'), reply_markup=_city_keyboard(lang, data.get('country', 'uz'), 'interflow_tocity_'))
    await callback.answer()


@router.callback_query(F.data.startswith('interflow_tocity_'), IntercityBotCreateFlow.to_city)
async def interflow_tocity_callback(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('interflow_tocity_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    await state.update_data(to_city=city)
    if data.get('inter_kind') == 'route':
        await state.set_state(IntercityBotCreateFlow.pickup_mode)
        await callback.message.answer(_ft(lang, 'pickup_mode'), reply_markup=_pickup_mode_keyboard(lang))
    else:
        await state.set_state(IntercityBotCreateFlow.date)
        await callback.message.answer(_ft(lang, 'enter_date'), reply_markup=_cancel_reply(lang))
    await callback.answer()


@router.message(IntercityBotCreateFlow.from_city)
async def interflow_fromcity_text(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    city = (message.text or '').strip()
    if not city:
        await message.answer(_ft(lang, 'select_from_city'))
        return
    data = await state.get_data()
    await state.update_data(from_city=city)
    await state.set_state(IntercityBotCreateFlow.to_city)
    await message.answer(_ft(lang, 'select_to_city'), reply_markup=_city_keyboard(lang, data.get('country', 'uz'), 'interflow_tocity_'))


@router.message(IntercityBotCreateFlow.to_city)
async def interflow_tocity_text(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    city = (message.text or '').strip()
    if not city:
        await message.answer(_ft(lang, 'select_to_city'))
        return
    data = await state.get_data()
    await state.update_data(to_city=city)
    if data.get('inter_kind') == 'route':
        await state.set_state(IntercityBotCreateFlow.pickup_mode)
        await message.answer(_ft(lang, 'pickup_mode'), reply_markup=_pickup_mode_keyboard(lang))
    else:
        await state.set_state(IntercityBotCreateFlow.date)
        await message.answer(_ft(lang, 'enter_date'), reply_markup=_cancel_reply(lang))


@router.callback_query(F.data.startswith('interflow_pickup_'), IntercityBotCreateFlow.pickup_mode)
async def interflow_pickup(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split('interflow_pickup_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(pickup_mode=mode)
    await state.set_state(IntercityBotCreateFlow.date)
    await callback.message.answer(_ft(lang, 'enter_date'), reply_markup=_cancel_reply(lang))
    await callback.answer()


@router.message(IntercityBotCreateFlow.date)
async def interflow_date(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    value = (message.text or '').strip()
    if not value:
        await message.answer(_ft(lang, 'enter_date'))
        return
    await state.update_data(date=value)
    await state.set_state(IntercityBotCreateFlow.time)
    await message.answer(_ft(lang, 'enter_time'), reply_markup=_cancel_reply(lang))


@router.message(IntercityBotCreateFlow.time)
async def interflow_time(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    value = (message.text or '').strip()
    if not value:
        await message.answer(_ft(lang, 'enter_time'))
        return
    await state.update_data(time=value)
    await state.set_state(IntercityBotCreateFlow.seats)
    await message.answer(_ft(lang, 'enter_seats'), reply_markup=_cancel_reply(lang))


@router.message(IntercityBotCreateFlow.seats)
async def interflow_seats(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    try:
        seats = max(1, int((message.text or '1').strip()))
    except Exception:
        await message.answer(_ft(lang, 'need_number'))
        return
    await state.update_data(seats=seats)
    await state.set_state(IntercityBotCreateFlow.price)
    await message.answer(_ft(lang, 'enter_price'), reply_markup=_cancel_reply(lang))


@router.message(IntercityBotCreateFlow.price)
async def interflow_price(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    try:
        price = float((message.text or '0').replace(',', '.').strip())
    except Exception:
        await message.answer(_ft(lang, 'need_number'))
        return
    await state.update_data(price=price)
    await state.set_state(IntercityBotCreateFlow.comment)
    await message.answer(_ft(lang, 'enter_comment'), reply_markup=_skip_or_cancel_reply(lang))


@router.message(IntercityBotCreateFlow.comment)
async def interflow_comment(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    comment = '' if (message.text or '').strip() == _ft(lang, 'skip') else (message.text or '').strip()
    try:
        if data.get('inter_kind') == 'route':
            row = await rq.create_intercity_route_bot(creator_tg_id=user.tg_id, country=data.get('country', user.country or 'uz'), from_city=data.get('from_city', ''), to_city=data.get('to_city', ''), date=data.get('date', ''), time=data.get('time', ''), seats=int(data.get('seats', 1) or 1), price=float(data.get('price', 0) or 0), comment=comment, pickup_mode=data.get('pickup_mode', 'ask_driver'))
            ok_text = _ft(lang, 'created_route_ok')
        else:
            row = await rq.create_intercity_request_bot(creator_tg_id=user.tg_id, country=data.get('country', user.country or 'uz'), from_city=data.get('from_city', ''), to_city=data.get('to_city', ''), date=data.get('date', ''), time=data.get('time', ''), seats_needed=int(data.get('seats', 1) or 1), price_offer=float(data.get('price', 0) or 0), comment=comment)
            ok_text = _ft(lang, 'created_request_ok')
    except Exception as exc:
        await message.answer(f"{_ft(lang, 'operation_failed')}\n{exc}", reply_markup=_remove_reply())
        return
    await state.clear()
    await message.answer(f"{ok_text}\n#{row.id}\n{row.from_city} → {row.to_city}\n{_lang_pack(lang)['price']}: {getattr(row, 'price', None) or getattr(row, 'price_offer', None) or 0}", reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))


@router.message(lambda m: m.text and any(m.text == MESSAGES[l].get('btn_cancel') for l in MESSAGES))
async def order_flow_cancel(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if not current or not current.startswith((CityBotCreateFlow.__name__, IntercityBotCreateFlow.__name__)):
        return
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await message.answer(_lang_pack(lang)['closed'], reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))

@router.callback_query(lambda callback: (callback.data or '').startswith(UNSUPPORTED_INLINE_PREFIXES))
async def unresolved_inline_fallback(callback: types.CallbackQuery):
    await callback.answer()
    lang = (await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)).language or 'ru'
    await callback.message.answer(_lang_pack(lang)['fallback'], reply_markup=_legacy_recovery_markup(lang, callback.data or ''))
