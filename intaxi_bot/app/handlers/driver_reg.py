import hashlib
import os
import secrets
from pathlib import Path

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from sqlalchemy import select

import app.database.requests as rq
import app.keyboards as kb
from app.miniapp_routes import profile_url
from app.strings import MESSAGES
from app.database.models import async_session, Vehicle

router = Router()
STORAGE_ROOT = Path('secure_driver_files')

LOCAL_TEXTS = {
    'ru': {'service_not_available':'Сервис недоступен для страны {country}','cancelled':'Регистрация водителя отменена.','approved':'✅ Ваша заявка одобрена. Теперь вы можете получать заказы.','approved_admin':'Заявка водителя {user_id} одобрена.','reject_reason_prompt':'Введите причину отказа (она будет отправлена водителю):','reject_sent':'Водителю {user_id} отправлен отказ с причиной.','main_menu':'🏠','new_application':'🆕 Новая заявка!','reject_title':'❌ <b>Ваша заявка отклонена</b>\n\nПричина: {reason}','approve_btn':'✅ Одобрить','reject_btn':'❌ Отклонить','files_saved':'Файлы сохранены в защищённом виде.','commission_prompt':'Сервис работает без комиссии: 0%. Продолжить регистрацию водителя?','commission_yes':'✅ Согласен','commission_no':'❌ Не согласен','good_deeds':'Пусть Аллах сделает наши дела благими.','driver_card_title':'Карточка водителя','driver_vehicle_media':'Фото машины'},
    'uz': {'service_not_available':'Xizmat {country} uchun mavjud emas','cancelled':'Haydovchi ro‘yxatdan o‘tishi bekor qilindi.','approved':'✅ Arizangiz tasdiqlandi. Endi buyurtmalarni olishingiz mumkin.','approved_admin':'{user_id} haydovchi arizasi tasdiqlandi.','reject_reason_prompt':'Rad etish sababini kiriting (u haydovchiga yuboriladi):','reject_sent':'{user_id} haydovchiga rad sababi yuborildi.','main_menu':'🏠','new_application':'🆕 Yangi ariza!','reject_title':'❌ <b>Arizangiz rad etildi</b>\n\nSabab: {reason}','approve_btn':'✅ Tasdiqlash','reject_btn':'❌ Rad etish','files_saved':'Fayllar himoyalangan ko‘rinishda saqlandi.','commission_prompt':'Xizmat 0% komissiya bilan ishlaydi. Haydovchi ro‘yxatidan o‘tishni davom ettirasizmi?','commission_yes':'✅ Roziman','commission_no':'❌ Rozi emasman','good_deeds':'Alloh ishlarimizni xayrli qilsin.','driver_card_title':'Haydovchi kartasi','driver_vehicle_media':'Mashina rasmlari'},
    'en': {'service_not_available':'Service is not available for {country}','cancelled':'Driver registration cancelled.','approved':'✅ Your application has been approved. You can receive orders now.','approved_admin':'Driver application {user_id} approved.','reject_reason_prompt':'Enter the reason for rejection (it will be sent to the driver):','reject_sent':'Rejection reason sent to driver {user_id}.','main_menu':'🏠','new_application':'🆕 New application!','reject_title':'❌ <b>Your application was rejected</b>\n\nReason: {reason}','approve_btn':'✅ Approve','reject_btn':'❌ Reject','files_saved':'Files were stored in protected form.','commission_prompt':'The service works with 0% commission. Continue driver registration?','commission_yes':'✅ I agree','commission_no':'❌ I do not agree','good_deeds':'May God make our deeds righteous.','driver_card_title':'Driver card','driver_vehicle_media':'Vehicle photos'},
    'ar': {'service_not_available':'الخدمة غير متاحة للدولة {country}','cancelled':'تم إلغاء تسجيل السائق.','approved':'✅ تمت الموافقة على طلبك. يمكنك الآن استلام الطلبات.','approved_admin':'تمت الموافقة على طلب السائق {user_id}.','reject_reason_prompt':'أدخل سبب الرفض (سيتم إرساله إلى السائق):','reject_sent':'تم إرسال سبب الرفض إلى السائق {user_id}.','main_menu':'🏠','new_application':'🆕 طلب جديد!','reject_title':'❌ <b>تم رفض طلبك</b>\n\nالسبب: {reason}','approve_btn':'✅ قبول','reject_btn':'❌ رفض','files_saved':'تم حفظ الملفات بشكل محمي.','commission_prompt':'الخدمة تعمل بعمولة 0%. هل تريد متابعة تسجيل السائق؟','commission_yes':'✅ أوافق','commission_no':'❌ لا أوافق','good_deeds':'نسأل الله أن يجعل أعمالنا صالحة.','driver_card_title':'بطاقة السائق','driver_vehicle_media':'صور السيارة'},
}

def tr(lang: str, key: str, default: str = '') -> str:
    return LOCAL_TEXTS.get(lang, LOCAL_TEXTS['ru']).get(key) or MESSAGES.get(lang, MESSAGES['ru']).get(key) or MESSAGES['ru'].get(key) or default


async def notify_admin_targets(bot: Bot, permission: str, *, text: str | None = None, media_group=None, reply_markup=None, parse_mode: str | None = 'HTML'):
    admin_ids = await rq.get_admin_targets_by_permission(permission)
    for admin_id in admin_ids:
        try:
            if media_group:
                await bot.send_media_group(admin_id, media_group)
            if text:
                await bot.send_message(admin_id, text, reply_markup=reply_markup, parse_mode=parse_mode, disable_web_page_preview=True)
        except Exception:
            pass


def cancel_reply_kb(lang: str):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=MESSAGES[lang].get('btn_cancel', '❌ Cancel'))]], resize_keyboard=True, one_time_keyboard=True)


def _driver_folder(tg_id: int) -> Path:
    secret = os.getenv('DRIVER_FILES_SECRET') or os.getenv('BOT_TOKEN') or 'intaxi-default-secret'
    folder_name = hashlib.sha256(f'{tg_id}:{secret}'.encode()).hexdigest()[:32]
    path = STORAGE_ROOT / folder_name
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _save_encrypted_telegram_file(bot: Bot, file_id: str, tg_id: int, logical_name: str) -> str:
    folder = _driver_folder(tg_id)
    telegram_file = await bot.get_file(file_id)
    ext = os.path.splitext(telegram_file.file_path)[1] or '.bin'
    path = folder / f"{logical_name}_{secrets.token_hex(8)}{ext}"
    await bot.download(file_id, destination=path)
    return str(path)


class DriverReg(StatesGroup):
    commission_agreement = State()
    brand = State()
    model = State()
    plate = State()
    color = State()
    capacity = State()
    photo_front = State()
    photo_back = State()
    photo_left = State()
    photo_right = State()
    waiting_for_reject_reason = State()


async def _cleanup_context(bot: Bot, user_tg_id: int, context: str) -> None:
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


@router.message(lambda message: any(message.text == MESSAGES[l].get('become_driver') for l in MESSAGES))
async def driver_reg_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    async with async_session() as session:
        existing = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
        if existing and user.is_verified:
            sent = await message.answer(MESSAGES[lang].get('moderation', 'Ваша заявка уже подтверждена.'))
            await _track(sent, 'driver_reg')
            return
    country_models = MESSAGES[lang].get('models', {}).get(user.country, {})
    if not country_models:
        sent = await message.answer(tr(lang, 'service_not_available').format(country=user.country))
        await _track(sent, 'driver_reg')
        return
    await _cleanup_context(message.bot, message.from_user.id, 'driver_reg')
    sent = await message.answer(tr(lang, 'commission_prompt'))
    await _track(sent, 'driver_reg')
    await _start_brand_flow(message, state, user)


async def _start_brand_flow(target, state: FSMContext, user):
    lang = user.language or 'ru'
    country_models = MESSAGES[lang].get('models', {}).get(user.country, {})
    builder = InlineKeyboardBuilder()
    for brand in country_models.keys():
        builder.button(text=brand, callback_data=f'brand_{brand}')
    builder.button(text=MESSAGES[lang].get('btn_cancel', '❌ Cancel'), callback_data='driverreg_cancel')
    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(MESSAGES[lang].get('enter_brand', 'Выберите марку автомобиля:'), reply_markup=builder.adjust(2).as_markup())
        await target.answer()
    else:
        sent = await target.answer(MESSAGES[lang].get('enter_brand', 'Выберите марку автомобиля:'), reply_markup=builder.adjust(2).as_markup())
        await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.brand)


@router.callback_query(F.data == 'driveragree_yes', DriverReg.commission_agreement)
async def driver_agree_yes(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    await _start_brand_flow(callback, state, user)


@router.callback_query(F.data == 'driveragree_no', DriverReg.commission_agreement)
@router.callback_query(F.data == 'driverreg_cancel')
async def driver_cancel(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    await callback.message.edit_text(tr(lang, 'cancelled'))
    await callback.message.answer('🏠', reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))
    await callback.answer()


@router.message(lambda m: m.text and any(m.text == MESSAGES[l].get('btn_cancel') for l in MESSAGES))
async def driver_cancel_by_text(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if not current or not current.startswith(DriverReg.__name__):
        return
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.clear()
    sent = await message.answer(tr(lang, 'cancelled'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))
    await _track(sent, 'driver_reg')


@router.callback_query(F.data.startswith('brand_'), DriverReg.brand)
async def reg_brand(callback: types.CallbackQuery, state: FSMContext):
    brand = callback.data.split('_', 1)[1]
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(brand=brand)
    builder = InlineKeyboardBuilder()
    models = MESSAGES[lang].get('models', {}).get(user.country, {}).get(brand, [])
    for m in models:
        builder.button(text=m, callback_data=f'model_{m}')
    builder.button(text=MESSAGES[lang].get('btn_cancel', '❌ Cancel'), callback_data='driverreg_cancel')
    await callback.message.edit_text(MESSAGES[lang].get('enter_model', 'Выберите модель автомобиля:'), reply_markup=builder.adjust(2).as_markup())
    await state.set_state(DriverReg.model)
    await callback.answer()


@router.callback_query(F.data.startswith('model_'), DriverReg.model)
async def reg_model(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(model=callback.data.split('_', 1)[1])
    await callback.message.edit_text(MESSAGES[lang].get('enter_plate', 'Введите номер автомобиля:'))
    sent = await callback.message.answer('⬇️', reply_markup=cancel_reply_kb(lang))
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.plate)
    await callback.answer()


@router.message(DriverReg.plate)
async def reg_plate(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    plate = (message.text or '').strip()
    if len(plate) < 4:
        sent = await message.answer(MESSAGES[lang].get('plate_error', 'Номер слишком короткий.'))
        await _track(sent, 'driver_reg')
        return
    await state.update_data(plate=plate)
    sent = await message.answer(MESSAGES[lang].get('enter_color', 'Введите цвет автомобиля:'), reply_markup=cancel_reply_kb(lang))
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.color)


@router.message(DriverReg.color)
async def reg_color(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(color=(message.text or '').strip())
    builder = InlineKeyboardBuilder()
    for c in ('4', '6', '8+'):
        builder.button(text=f'🚐 {c}', callback_data=f'cap_{c}')
    builder.button(text=MESSAGES[lang].get('btn_cancel', '❌ Cancel'), callback_data='driverreg_cancel')
    sent = await message.answer(MESSAGES[lang].get('select_cap', 'Выберите вместимость автомобиля:'), reply_markup=builder.adjust(2).as_markup())
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.capacity)


@router.callback_query(F.data.startswith('cap_'), DriverReg.capacity)
async def reg_cap(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    await state.update_data(capacity=callback.data.split('_', 1)[1])
    await callback.message.edit_text(MESSAGES[lang].get('photo_front', 'Отправьте фото автомобиля спереди, чтобы номер был хорошо виден.'))
    sent = await callback.message.answer('⬇️', reply_markup=cancel_reply_kb(lang))
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.photo_front)
    await callback.answer()


@router.message(DriverReg.photo_front, F.photo)
async def reg_photo_front(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    file_id = message.photo[-1].file_id
    file_path = await _save_encrypted_telegram_file(message.bot, file_id, message.from_user.id, 'photo_front')
    await state.update_data(photo_front=file_id, photo_front_path=file_path, photo_tech=file_id, photo_tech_path=file_path)
    sent = await message.answer(MESSAGES[lang].get('photo_back', 'Отправьте фото автомобиля сзади, чтобы номер был хорошо виден.'), reply_markup=cancel_reply_kb(lang))
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.photo_back)


@router.message(DriverReg.photo_back, F.photo)
async def reg_photo_back(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    file_id = message.photo[-1].file_id
    file_path = await _save_encrypted_telegram_file(message.bot, file_id, message.from_user.id, 'photo_back')
    await state.update_data(photo_back=file_id, photo_back_path=file_path, photo_license=file_id, photo_license_path=file_path)
    sent = await message.answer(MESSAGES[lang].get('photo_left', 'Отправьте фото автомобиля слева.'), reply_markup=cancel_reply_kb(lang))
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.photo_left)


@router.message(DriverReg.photo_left, F.photo)
async def reg_photo_left(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    file_id = message.photo[-1].file_id
    file_path = await _save_encrypted_telegram_file(message.bot, file_id, message.from_user.id, 'photo_left')
    await state.update_data(photo_left=file_id, photo_left_path=file_path, photo_out=file_id, photo_out_path=file_path)
    sent = await message.answer(MESSAGES[lang].get('photo_right', 'Отправьте фото автомобиля справа.'), reply_markup=cancel_reply_kb(lang))
    await _track(sent, 'driver_reg')
    await state.set_state(DriverReg.photo_right)


@router.message(DriverReg.photo_right, F.photo)
async def reg_photo_right(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    file_id = message.photo[-1].file_id
    file_path = await _save_encrypted_telegram_file(message.bot, file_id, message.from_user.id, 'photo_right')
    await state.update_data(photo_right=file_id, photo_right_path=file_path, photo_in=file_id, photo_in_path=file_path)
    data = await state.get_data()
    await rq.register_vehicle(message.from_user.id, data)
    await state.clear()
    sent = await message.answer(MESSAGES[lang].get('moderation', 'Ваша заявка отправлена на модерацию.'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger')))
    await _track(sent, 'driver_reg')

    media_items = []
    for key in ('photo_front', 'photo_back', 'photo_left', 'photo_right'):
        value = data.get(key)
        if value:
            media_items.append(InputMediaPhoto(media=value))
    await notify_admin_targets(bot, 'moderation', media_group=media_items or None)

    admin_lang = 'ru'
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(admin_lang, 'approve_btn'), callback_data=f'verify_{message.from_user.id}')
    builder.button(text=tr(admin_lang, 'reject_btn'), callback_data=f'reject_{message.from_user.id}')
    builder.adjust(2)

    username_value = getattr(user, 'username', None) or message.from_user.username
    if username_value:
        username_line = f"👤 Username: <a href=\"https://t.me/{username_value}\">@{username_value}</a>"
    else:
        username_line = f"👤 Username: —\n📨 <a href=\"tg://user?id={message.from_user.id}\">Открыть чат</a>"

    text = (
        f"{tr(admin_lang, 'new_application')}\n"
        f"ID: <code>{message.from_user.id}</code>\n"
        f"{username_line}\n"
        f"Авто: {data['brand']} {data['model']} ({data['plate']})\n"
        f"📷 4 фото машины получены\n"
        f"🔐 {tr(admin_lang, 'files_saved')}"
    )
    await notify_admin_targets(bot, 'moderation', text=text, reply_markup=builder.as_markup(), parse_mode='HTML')


@router.callback_query(F.data.startswith('verify_'))
async def verify_driver_callback(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_', 1)[1])
    await rq.verify_driver(user_id)
    target = await rq.get_or_create_user(user_id, '')
    lang = target.language or 'ru'
    await callback.answer('OK')
    await callback.message.answer(tr('ru', 'approved_admin').format(user_id=user_id))
    try:
        await callback.bot.send_message(user_id, tr(lang, 'approved'), reply_markup=kb.main_menu(lang, user_id=user_id, as_user=True, is_driver_mode=True))
    except Exception:
        pass


@router.callback_query(F.data.startswith('reject_'))
async def reject_driver_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split('_', 1)[1])
    await state.set_state(DriverReg.waiting_for_reject_reason)
    await state.update_data(reject_user_id=user_id)
    await callback.message.answer(tr('ru', 'reject_reason_prompt'))
    await callback.answer()


@router.message(DriverReg.waiting_for_reject_reason)
async def reject_driver_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = int(data.get('reject_user_id', 0))
    reason = (message.text or '').strip()
    if user_id:
        await rq.reject_user_vehicle(user_id)
        target = await rq.get_or_create_user(user_id, '')
        lang = target.language or 'ru'
        try:
            await message.bot.send_message(user_id, tr(lang, 'reject_title').format(reason=reason), parse_mode='HTML')
        except Exception:
            pass
    await state.clear()
    await message.answer(tr('ru', 'reject_sent').format(user_id=user_id))
