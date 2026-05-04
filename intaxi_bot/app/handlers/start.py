from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.database.requests as rq
import app.keyboards as kb
from app.hotfix_menu import home_webapp_menu
from app.kazakhstan_locations import build_localities_keyboard as build_kz_localities_keyboard, build_regions_keyboard as build_kz_regions_keyboard, format_kz_location, get_locality_by_index as get_kz_locality_by_index
from app.miniapp_routes import profile_url
from app.strings import MESSAGES
from app.uzbekistan_locations import build_regions_keyboard, build_localities_keyboard, format_uz_location, get_locality_by_index

router = Router()

BISMILLAH_TEXTS = {
    'ru': 'Во имя Аллаха, Милостивого, Милующего.',
    'uz': 'Mehribon va Rahmli Alloh nomi bilan.',
    'en': 'In the name of God, the Most Compassionate, the Most Merciful.',
    'ar': 'بسم الله الرحمن الرحيم',
}

PRIVACY_NOTICE_TEXTS = {
    'ru': 'Мы не собираем ваши личные документы и не запрашиваем лишние персональные данные. Для работы сервиса используются только те публичные данные, которые Telegram предоставляет приложению.',
    'uz': 'Biz sizning shaxsiy hujjatlaringizni yig‘maymiz va ortiqcha shaxsiy ma’lumotlarni so‘ramaymiz. Xizmat ishlashi uchun faqat Telegram ilovaga taqdim etadigan ochiq ma’lumotlardan foydalaniladi.',
    'en': 'We do not collect your personal documents or request unnecessary personal data. The service uses only the public data that Telegram provides to the application.',
    'ar': 'نحن لا نجمع مستنداتك الشخصية ولا نطلب بيانات شخصية غير لازمة. ولتشغيل الخدمة نستخدم فقط البيانات العامة التي يوفّرها تيليجرام للتطبيق.',
}

COUNTRY_LABELS = {
    'ru': {'uz': 'Узбекистан', 'tr': 'Турция', 'kz': 'Казахстан', 'sa': 'Саудовская Аравия'},
    'uz': {'uz': 'O‘zbekiston', 'tr': 'Turkiya', 'kz': 'Qozog‘iston', 'sa': 'Saudiya Arabistoni'},
    'en': {'uz': 'Uzbekistan', 'tr': 'Turkey', 'kz': 'Kazakhstan', 'sa': 'Saudi Arabia'},
    'ar': {'uz': 'أوزبكستان', 'tr': 'تركيا', 'kz': 'كازاخستان', 'sa': 'السعودية'},
}

WELCOME = (
    'Xush kelibsiz! Tilni tanlang.\n'
    'Добро пожаловать! Выберите язык.\n'
    'Welcome! Choose your language.\n'
    'مرحبًا! اختر لغتك.'
)

USERNAME_REQUIRED_TEXT = (
    'Telegram username kerak.\n'
    'Требуется Telegram username.\n'
    'A Telegram username is required.\n'
    'مطلوب اسم مستخدم في تيليجرام.'
)


class Reg(StatesGroup):
    language = State()
    country = State()
    region = State()
    city = State()


async def _cleanup_context(bot, user_tg_id: int, context: str) -> None:
    rows = await rq.get_cleanup_messages(user_tg_id, context)
    for row in rows:
        try:
            await bot.delete_message(chat_id=row.chat_id, message_id=row.message_id)
        except Exception:
            pass
    await rq.clear_cleanup_messages(user_tg_id, context)


async def _track(message: types.Message, context: str) -> None:
    try:
        await rq.track_cleanup_message(message.from_user.id, message.chat.id, message.message_id, context)
    except Exception:
        pass


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    if not message.from_user.username:
        sent = await message.answer(USERNAME_REQUIRED_TEXT)
        await _track(sent, 'start')
        sent = await message.answer(MESSAGES['ru'].get('username_required_guide', 'Telegram → Settings → Username'))
        await _track(sent, 'start')
        return
    if user.language and user.country and user.city:
        await _cleanup_context(message.bot, user.tg_id, 'start')
        sent = await message.answer(
            '🏠',
            reply_markup=home_webapp_menu(
                user.language,
                is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger'),
            ),
        )
        await _track(sent, 'anchor')
        return
    await _cleanup_context(message.bot, message.from_user.id, 'start')
    sent = await message.answer(WELCOME, reply_markup=kb.language_kb)
    await _track(sent, 'start')
    await state.set_state(Reg.language)


@router.message(Reg.language)
async def set_language(message: types.Message, state: FSMContext):
    lang_map = {
        '🇷🇺 Русский': 'ru',
        "🇺🇿 O'zbekcha": 'uz',
        '🇬🇧 English': 'en',
        '🇸🇦 العربية': 'ar',
    }
    lang = lang_map.get(message.text or '')
    if not lang:
        return
    await state.update_data(language=lang)
    await _cleanup_context(message.bot, message.from_user.id, 'start')
    sent = await message.answer(BISMILLAH_TEXTS.get(lang, BISMILLAH_TEXTS['ru']))
    await _track(sent, 'start')
    sent = await message.answer(PRIVACY_NOTICE_TEXTS.get(lang, PRIVACY_NOTICE_TEXTS['ru']))
    await _track(sent, 'start')
    builder = InlineKeyboardBuilder()
    for code, local_name in COUNTRY_LABELS.get(lang, COUNTRY_LABELS['ru']).items():
        builder.button(text=local_name, callback_data=f'country_{code}')
    builder.adjust(1)
    sent = await message.answer(MESSAGES[lang].get('select_country', 'Select country:'), reply_markup=builder.as_markup())
    await _track(sent, 'start')
    await state.set_state(Reg.country)


@router.callback_query(F.data.startswith('country_'), Reg.country)
async def set_country(callback: types.CallbackQuery, state: FSMContext):
    country_code = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data['language']
    await state.update_data(country=country_code)
    if country_code == 'uz':
        builder = build_regions_keyboard(lang, 'uzregion_')
        await callback.message.edit_text(MESSAGES[lang].get('select_region', 'Select region:'), reply_markup=builder.as_markup())
        await state.set_state(Reg.region)
        await callback.answer()
        return
    if country_code == 'kz':
        builder = build_kz_regions_keyboard(lang, 'kzregion_')
        await callback.message.edit_text(MESSAGES[lang].get('select_region', 'Select region:'), reply_markup=builder.as_markup())
        await state.set_state(Reg.region)
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for city in MESSAGES[lang].get('cities', {}).get(country_code, []):
        builder.button(text=city, callback_data=f'city_{city}')
    builder.button(
        text=MESSAGES[lang].get('btn_other_city', 'Other city (Mini App)'),
        web_app=types.WebAppInfo(url=profile_url('other-city')),
    )
    builder.adjust(2)
    await callback.message.edit_text(MESSAGES[lang].get('select_city', 'Select city:'), reply_markup=builder.as_markup())
    await state.set_state(Reg.city)
    await callback.answer()


@router.callback_query(F.data.startswith('uzregion_'), Reg.region)
async def set_uz_region(callback: types.CallbackQuery, state: FSMContext):
    region_key = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data['language']
    await state.update_data(region=region_key)
    builder = build_localities_keyboard(region_key, lang, 'uzcity_')
    await callback.message.edit_text(MESSAGES[lang].get('select_district_city', 'Select district or city:'), reply_markup=builder.as_markup())
    await state.set_state(Reg.city)
    await callback.answer()


@router.callback_query(F.data.startswith('kzregion_'), Reg.region)
async def set_kz_region(callback: types.CallbackQuery, state: FSMContext):
    region_key = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data['language']
    await state.update_data(region=region_key)
    builder = build_kz_localities_keyboard(region_key, lang, 'kzcity_')
    await callback.message.edit_text(MESSAGES[lang].get('select_district_city', 'Select district or city:'), reply_markup=builder.as_markup())
    await state.set_state(Reg.city)
    await callback.answer()


@router.callback_query(F.data.startswith('city_'), Reg.city)
async def set_city(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data['language']
    await rq.set_user_reg(callback.from_user.id, lang, data['country'], city)
    await state.clear()
    await callback.answer(MESSAGES[lang].get('reg_done', 'Done!'))
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    await callback.message.answer(
        MESSAGES[lang].get('reg_done', 'Done!'),
        reply_markup=home_webapp_menu(
            lang,
            is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger'),
        ),
    )


@router.callback_query(F.data.startswith('uzcity_'), Reg.city)
async def set_uz_city(callback: types.CallbackQuery, state: FSMContext):
    payload = callback.data.split('_', 1)[1]
    region_key, idx_raw = payload.split(':', 1)
    data = await state.get_data()
    lang = data['language']
    locality = get_locality_by_index(region_key, lang, int(idx_raw))
    city_value = format_uz_location(region_key, locality, lang)
    await rq.set_user_reg(callback.from_user.id, lang, data['country'], city_value)
    await state.clear()
    await callback.answer(MESSAGES[lang].get('reg_done', 'Done!'))
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    await callback.message.answer(
        MESSAGES[lang].get('reg_done', 'Done!'),
        reply_markup=home_webapp_menu(
            lang,
            is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger'),
        ),
    )


@router.callback_query(F.data.startswith('kzcity_'), Reg.city)
async def set_kz_city(callback: types.CallbackQuery, state: FSMContext):
    payload = callback.data.split('_', 1)[1]
    region_key, idx_raw = payload.split(':', 1)
    data = await state.get_data()
    lang = data['language']
    locality = get_kz_locality_by_index(region_key, lang, int(idx_raw))
    city_value = format_kz_location(region_key, locality, lang)
    await rq.set_user_reg(callback.from_user.id, lang, data['country'], city_value)
    await state.clear()
    await callback.answer(MESSAGES[lang].get('reg_done', 'Done!'))
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    await callback.message.answer(
        MESSAGES[lang].get('reg_done', 'Done!'),
        reply_markup=home_webapp_menu(
            lang,
            is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger'),
        ),
    )
