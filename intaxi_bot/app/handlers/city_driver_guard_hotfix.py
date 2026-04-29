from __future__ import annotations

from aiogram import Router, types
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext

import app.database.requests as rq
import app.keyboards as kb
from app.handlers.live_city_hotfix import CityCreateFlow
from app.hotfix_menu import home_webapp_menu
from app.miniapp_routes import city_main_url, profile_url
from app.strings import MESSAGES

router = Router()


def _match_button(message_text: str | None, key: str) -> bool:
    if not message_text:
        return False
    for msgs in MESSAGES.values():
        if message_text == msgs.get(key):
            return True
    return False


def _cancel_texts() -> set[str]:
    result: set[str] = set()
    for msgs in MESSAGES.values():
        if msgs.get('btn_cancel'):
            result.add(msgs['btn_cancel'])
    return result


CANCEL_TEXTS = _cancel_texts()


def _driver_mode(user) -> bool:
    return bool(user.is_verified and (user.active_role or 'driver') != 'passenger')


def _guide(lang: str) -> tuple[str, str, str]:
    if lang == 'uz':
        return (
            'Haydovchi uchun tez buyurtma o‘chirilgan.',
            'Agar haydovchi o‘zi uchun taksi chaqirmoqchi bo‘lsa, profilga kirib rolni yo‘lovchiga almashtirishi kerak.',
            'Profilni ochish',
        )
    if lang == 'ar':
        return (
            'تم إيقاف الطلب السريع للسائق.',
            'إذا أراد السائق طلب سيارة لنفسه، فعليه فتح الملف الشخصي وتبديل الدور إلى راكب.',
            'فتح الملف الشخصي',
        )
    if lang == 'kz':
        return (
            'Жүргізушіге жылдам тапсырыс өшірілген.',
            'Егер жүргізуші өзі үшін такси шақырғысы келсе, профильге кіріп рөлін жолаушыға ауыстыруы керек.',
            'Профильді ашу',
        )
    if lang == 'en':
        return (
            'Fast order is disabled for drivers.',
            'If a driver wants to order a taxi, they need to open the profile and switch the role to passenger.',
            'Open profile',
        )
    return (
        'Быстрый заказ для водителя отключён.',
        'Если водитель хочет заказать такси для себя, нужно открыть профиль и переключить роль на пассажира.',
        'Открыть профиль',
    )


@router.message(lambda message: _match_button(message.text, 'btn_fast_order'))
async def prevent_driver_fast_order(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    if not _driver_mode(user):
        raise SkipHandler()
    await state.clear()
    lang = user.language or 'ru'
    title, text, button = _guide(lang)
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=button, web_app=types.WebAppInfo(url=profile_url()))],
            [types.InlineKeyboardButton(text='📱 Mini App', web_app=types.WebAppInfo(url=city_main_url('driver')))],
        ]
    )
    await message.answer(f'{title}\n\n{text}', reply_markup=markup)


@router.message(CityCreateFlow.pickup)
@router.message(CityCreateFlow.destination)
@router.message(CityCreateFlow.seats)
@router.message(CityCreateFlow.price)
@router.message(CityCreateFlow.comment)
@router.message(CityCreateFlow.offer_price)
async def cancel_live_city_flow(message: types.Message, state: FSMContext):
    if (message.text or '') not in CANCEL_TEXTS:
        raise SkipHandler()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await message.answer('✅ Отменено.', reply_markup=home_webapp_menu(lang, is_driver_mode=_driver_mode(user)))
