from __future__ import annotations

import html

from aiogram import F, Bot, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.database.requests as rq
import app.keyboards as kb
import app.order_actions as order_actions
from app.miniapp_routes import city_main_url, current_trip_url, intercity_main_url
from app.strings import MESSAGES

router = Router()

TEXTS = {
    'ru': {
        'current_trip': '📌 Текущая поездка', 'open_city': 'Открыть город', 'open_intercity': 'Открыть межгород',
        'moved_to_miniapp': 'Этот сценарий переведён в Mini App. Откройте актуальный раздел ниже.',
        'complaint_prompt': 'Напишите жалобу одним сообщением. Она будет отправлена администраторам.',
        'complaint_new': 'Новая жалоба', 'from_user': 'От', 'target': 'Цель', 'text': 'Текст', 'complaint_sent': '✅ Жалоба отправлена.',
        'not_found': 'Не найдено или нет доступа', 'city_order_closed': 'Городской заказ #{id} закрыт.',
    },
    'uz': {
        'current_trip': '📌 Joriy safar', 'open_city': 'Shaharni ochish', 'open_intercity': 'Shaharlararoni ochish',
        'moved_to_miniapp': 'Bu ssenariy Mini Appga o‘tkazilgan. Quyidagi aktual bo‘limni oching.',
        'complaint_prompt': 'Shikoyatni bitta xabar bilan yozing. U administratorlarga yuboriladi.',
        'complaint_new': 'Yangi shikoyat', 'from_user': 'Kimdan', 'target': 'Maqsad', 'text': 'Matn', 'complaint_sent': '✅ Shikoyat yuborildi.',
        'not_found': 'Topilmadi yoki ruxsat yo‘q', 'city_order_closed': 'Shahar buyurtmasi #{id} yopildi.',
    },
    'en': {
        'current_trip': '📌 Current trip', 'open_city': 'Open city', 'open_intercity': 'Open intercity',
        'moved_to_miniapp': 'This scenario has been moved to the Mini App. Open the current section below.',
        'complaint_prompt': 'Send your complaint in one message. It will be forwarded to the admins.',
        'complaint_new': 'New complaint', 'from_user': 'From', 'target': 'Target', 'text': 'Text', 'complaint_sent': '✅ Complaint sent.',
        'not_found': 'Not found or access denied', 'city_order_closed': 'City order #{id} has been closed.',
    },
    'ar': {
        'current_trip': '📌 الرحلة الحالية', 'open_city': 'فتح المدينة', 'open_intercity': 'فتح بين المدن',
        'moved_to_miniapp': 'تم نقل هذا السيناريو إلى Mini App. افتح القسم الحالي أدناه.',
        'complaint_prompt': 'اكتب الشكوى في رسالة واحدة. سيتم إرسالها إلى المشرفين.',
        'complaint_new': 'شكوى جديدة', 'from_user': 'من', 'target': 'الهدف', 'text': 'النص', 'complaint_sent': '✅ تم إرسال الشكوى.',
        'not_found': 'غير موجود أو لا توجد صلاحية', 'city_order_closed': 'تم إغلاق طلب المدينة #{id}.',
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
