from __future__ import annotations

import html

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

import app.database.requests as rq
import app.keyboards as kb
from app.country_config import country_code_from_address
from app.database.models import DriverOnlineState, User, Vehicle, async_session
from app.handlers.profile import _extract_geo_city, _profile_location_kb, _reverse_geocode_sync, is_driver_mode, tr
from app.miniapp_routes import profile_url
from app.strings import MESSAGES
from app.uzbekistan_locations import build_localities_keyboard, build_regions_keyboard, format_uz_location, get_locality_by_index

router = Router()


class EditProfile(StatesGroup):
    language = State()
    country = State()
    region = State()
    city = State()


async def _vehicle_for_user(user: User) -> Vehicle | None:
    async with async_session() as session:
        return await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))


async def _set_driver_offline(tg_id: int) -> None:
    async with async_session() as session:
        row = await session.scalar(select(DriverOnlineState).where(DriverOnlineState.driver_tg_id == tg_id))
        if row:
            row.is_online = False
            await session.commit()


@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_edit_data'] for x in kb.LOCAL_DEFAULTS])
async def open_edit_data_menu(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    vehicle = await _vehicle_for_user(user)
    show_toggle = bool(vehicle and getattr(vehicle, 'vehicle_class', 'class4') == 'class7')
    class4_enabled = bool(vehicle and getattr(vehicle, 'accepts_class4', True))
    await message.answer(
        tr(lang, 'edit_data_title'),
        reply_markup=kb.edit_data_menu(
            lang,
            is_driver=bool(vehicle),
            show_become_driver=(not bool(vehicle) and not user.is_verified),
            show_class4_toggle=show_toggle,
            class4_enabled=class4_enabled,
            show_role_toggle=bool(vehicle and user.is_verified),
            active_role=(user.active_role or 'driver'),
        ),
    )


@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_change_language'] for x in kb.LOCAL_DEFAULTS])
async def change_language_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.set_state(EditProfile.language)
    await message.answer(tr(lang, 'choose_language'), reply_markup=kb.language_kb)


@router.message(EditProfile.language)
async def change_language_finish(message: types.Message, state: FSMContext):
    lang_map = {'🇷🇺 Русский': 'ru', '🇺🇿 O\'zbekcha': 'uz', '🇬🇧 English': 'en', '🇸🇦 العربية': 'ar'}
    lang = lang_map.get(message.text)
    if not lang:
        return
    await rq.update_user_language(message.from_user.id, lang)
    await state.clear()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(tr(lang, 'language_changed'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_change_location'] for x in kb.LOCAL_DEFAULTS])
async def change_location_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await state.update_data(language=lang)
    await state.set_state(EditProfile.country)
    builder = InlineKeyboardBuilder()
    for code, local_name in MESSAGES[lang].get('countries', {}).items():
        builder.button(text=local_name, callback_data=f'editcountry_{code}')
    builder.adjust(1)
    await message.answer(tr(lang, 'select_country'), reply_markup=builder.as_markup())
    await message.answer(tr(lang, 'share_location'), reply_markup=_profile_location_kb(lang))


@router.message(EditProfile.country, F.location)
@router.message(EditProfile.city, F.location)
async def edit_location_from_geo(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    try:
        lat = round(message.location.latitude, 6)
        lng = round(message.location.longitude, 6)
        data = _reverse_geocode_sync(lat, lng)
        address = data.get('address') or {}
        country_code = country_code_from_address(address)
        city = _extract_geo_city(address) or user.city or f'{lat}, {lng}'
        await rq.update_user_country_city(message.from_user.id, country_code, city)
        await state.clear()
        detected_address = html.escape(str(data.get('display_name') or city))
        detected_coords = html.escape(f'{lat}, {lng}')
        await message.answer(
            f"{tr(lang, 'location_changed')}\n\n{tr(lang, 'detected_address')}: {detected_address}\n{tr(lang, 'detected_coords')}: <code>{detected_coords}</code>",
            parse_mode='HTML',
            reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)),
        )
    except Exception:
        await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.callback_query(F.data.startswith('editcountry_'), EditProfile.country)
async def edit_country_pick(callback: types.CallbackQuery, state: FSMContext):
    country_code = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data.get('language') or 'ru'
    await state.update_data(country=country_code)
    if country_code == 'uz':
        builder = build_regions_keyboard(lang, 'edituzregion_')
        await callback.message.edit_text(tr(lang, 'select_region'), reply_markup=builder.as_markup())
        await state.set_state(EditProfile.region)
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for city in MESSAGES[lang].get('cities', {}).get(country_code, []):
        builder.button(text=city, callback_data=f'editcity_{city}')
    builder.button(text=MESSAGES[lang].get('btn_other_city', 'Other city (Mini App)'), web_app=types.WebAppInfo(url=profile_url('edit-location')))
    builder.adjust(2)
    await callback.message.edit_text(tr(lang, 'select_city'), reply_markup=builder.as_markup())
    await state.set_state(EditProfile.city)
    await callback.answer()


@router.callback_query(F.data.startswith('edituzregion_'), EditProfile.region)
async def edit_uz_region_pick(callback: types.CallbackQuery, state: FSMContext):
    region_key = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data.get('language') or 'ru'
    await state.update_data(region=region_key)
    builder = build_localities_keyboard(region_key, lang, 'edituzcity_')
    await callback.message.edit_text(tr(lang, 'select_district_city'), reply_markup=builder.as_markup())
    await state.set_state(EditProfile.city)
    await callback.answer()


@router.callback_query(F.data.startswith('editcity_'), EditProfile.city)
async def edit_city_pick(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data.get('language') or 'ru'
    await rq.update_user_country_city(callback.from_user.id, data.get('country') or 'uz', city)
    await state.clear()
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    await callback.message.answer(tr(lang, 'location_changed'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
    await callback.answer()


@router.callback_query(F.data.startswith('edituzcity_'), EditProfile.city)
async def edit_uz_city_pick(callback: types.CallbackQuery, state: FSMContext):
    payload = callback.data.split('_', 1)[1]
    region_key, idx_raw = payload.split(':', 1)
    data = await state.get_data()
    lang = data.get('language') or 'ru'
    locality = get_locality_by_index(region_key, lang, int(idx_raw))
    city_value = format_uz_location(region_key, locality, lang)
    await rq.update_user_country_city(callback.from_user.id, data.get('country') or 'uz', city_value)
    await state.clear()
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    await callback.message.answer(tr(lang, 'location_changed'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
    await callback.answer()


@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_change_vehicle'] for x in kb.LOCAL_DEFAULTS])
async def change_vehicle_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    vehicle = await _vehicle_for_user(user)
    if not vehicle:
        return
    await _set_driver_offline(user.tg_id)
    await rq.remove_vehicle_for_edit(user.tg_id)
    await state.clear()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(MESSAGES[lang].get('moderation', 'Введите данные машины заново.'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=False))
    await message.answer(MESSAGES[lang].get('become_driver'))


@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x].get('btn_toggle_small_orders_on') for x in kb.LOCAL_DEFAULTS] + [kb.LOCAL_DEFAULTS[x].get('btn_toggle_small_orders_off') for x in kb.LOCAL_DEFAULTS])
async def toggle_small_orders_mode(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    vehicle = await rq.toggle_driver_accepts_class4(user.tg_id)
    if not vehicle:
        await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
        return
    key = 'toggle_small_orders_enabled' if vehicle.accepts_class4 else 'toggle_small_orders_disabled'
    await message.answer(MESSAGES[lang].get(key, key), reply_markup=kb.edit_data_menu(lang, is_driver=True, show_become_driver=False, show_class4_toggle=True, class4_enabled=vehicle.accepts_class4, show_role_toggle=True, active_role=(user.active_role or 'driver')))


@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_switch_role_to_passenger') for l in MESSAGES) or any(message.text == MESSAGES[l].get('btn_switch_role_to_driver') for l in MESSAGES))
async def toggle_driver_role_mode(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    vehicle = await _vehicle_for_user(user)
    if not (user.is_verified and vehicle):
        await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
        return
    new_role = 'passenger' if (user.active_role or 'driver') != 'passenger' else 'driver'
    user = await rq.set_user_active_role(user.tg_id, new_role)
    if new_role == 'passenger':
        await _set_driver_offline(user.tg_id)
    msg_key = 'role_switched_to_passenger' if new_role == 'passenger' else 'role_switched_to_driver'
    await message.answer(MESSAGES[lang].get(msg_key, msg_key), reply_markup=kb.edit_data_menu(lang, is_driver=True, show_become_driver=False, show_class4_toggle=(getattr(vehicle, 'vehicle_class', 'class4') == 'class7'), class4_enabled=bool(getattr(vehicle, 'accepts_class4', True)), show_role_toggle=True, active_role=new_role))
