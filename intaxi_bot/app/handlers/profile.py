from aiogram import Router, types, F, Bot
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import random
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import app.database.requests as rq
import app.keyboards as kb
from app.miniapp_routes import profile_url
from app.strings import MESSAGES
from app.database.models import async_session, Vehicle
from app.uzbekistan_locations import build_regions_keyboard, build_localities_keyboard, format_uz_location, get_locality_by_index
from sqlalchemy import select

router = Router()
AYAH_ROTATION = [
    {
        'ru': 'Коран 59:18 — О вы, которые уверовали! Бойтесь Аллаха, и пусть каждая душа посмотрит, что она приготовила на завтрашний день. Бойтесь Аллаха: поистине, Аллах ведает о том, что вы делаете.',
        'uz': 'Qur’on 59:18 — Ey iymon keltirganlar! Allohdan qo‘rqinglar. Har bir jon ertangi kun uchun nimani tayyorlaganiga nazar solsin. Allohdan qo‘rqinglar. Albatta, Alloh qilayotgan ishlaringizdan xabardordir.',
        'en': 'Quran 59:18 — O you who believe! Be mindful of Allah, and let every soul consider what it has prepared for tomorrow. Be mindful of Allah. Surely Allah is fully aware of all that you do.',
        'ar': 'القرآن 59:18 — يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَلْتَنْظُرْ نَفْسٌ مَا قَدَّمَتْ لِغَدٍ ۖ وَاتَّقُوا اللَّهَ ۚ إِنَّ اللَّهَ خَبِيرٌ بِمَا تَعْمَلُونَ.',
    },
    {
        'ru': 'Коран 5:1 — О вы, которые уверовали! Будьте верны договорам и обязательствам.',
        'uz': 'Qur’on 5:1 — Ey iymon keltirganlar! Ahd va bitimlarga sodiq bo‘linglar.',
        'en': 'Quran 5:1 — O you who believe! Honour your agreements and obligations.',
        'ar': 'القرآن 5:1 — يَا أَيُّهَا الَّذِينَ آمَنُوا أَوْفُوا بِالْعُقُودِ.',
    },
    {
        'ru': 'Коран 17:34 — Исполняйте обещание: поистине, за обещание будет спрошено.',
        'uz': 'Qur’on 17:34 — Ahdga vafo qilinglar. Albatta, ahd uchun javob beriladi.',
        'en': 'Quran 17:34 — Fulfil every pledge. Surely every pledge will be called to account.',
        'ar': 'القرآن 17:34 — وَأَوْفُوا بِالْعَهْدِ ۖ إِنَّ الْعَهْدَ كَانَ مَسْؤُولًا.',
    },
    {
        'ru': 'Коран 2:188 — Не присваивайте имущество друг друга несправедливо и не используйте это для неправомерного посягательства на чужое.',
        'uz': 'Qur’on 2:188 — Bir-biringizning molini nohaq yemanglar va gunoh yo‘li bilan o‘zgalarning haqqiga tajovuz qilmanglar.',
        'en': 'Quran 2:188 — Do not consume one another’s wealth unjustly, nor use it to wrongfully devour what belongs to others.',
        'ar': 'القرآن 2:188 — وَلَا تَأْكُلُوا أَمْوَالَكُمْ بَيْنَكُمْ بِالْبَاطِلِ.',
    },
    {
        'ru': 'Коран 4:58 — Аллах велит вам возвращать доверенное его владельцам, а когда вы судите между людьми — судить по справедливости.',
        'uz': 'Qur’on 4:58 — Alloh sizlarga omonatlarni egalariga topshirishni va odamlar orasida hukm qilsangiz, adolat bilan hukm qilishni buyuradi.',
        'en': 'Quran 4:58 — Allah commands you to return trusts to their owners and, when you judge between people, to judge with justice.',
        'ar': 'القرآن 4:58 — إِنَّ اللَّهَ يَأْمُرُكُمْ أَنْ تُؤَدُّوا الْأَمَانَاتِ إِلَى أَهْلِهَا وَإِذَا حَكَمْتُمْ بَيْنَ النَّاسِ أَنْ تَحْكُمُوا بِالْعَدْلِ.',
    },
    {
        'ru': 'Коран 49:11 — Не насмехайтесь друг над другом, не унижайте друг друга и не называйте друг друга обидными прозвищами.',
        'uz': 'Qur’on 49:11 — Bir-biringizni masxara qilmanglar, bir-biringizni kamsitmanglar va haqoratli laqablar bilan atamanglar.',
        'en': 'Quran 49:11 — Do not ridicule one another, do not defame one another, and do not call each other by offensive nicknames.',
        'ar': 'القرآن 49:11 — وَلَا تَلْمِزُوا أَنْفُسَكُمْ وَلَا تَنَابَزُوا بِالْأَلْقَابِ.',
    },
]

def ayah_header(lang: str) -> str:
    verse = random.choice(AYAH_ROTATION)
    return f"<i>{verse.get(lang, verse['ru'])}</i>\n\n"

ADMIN_RECEIVING_CARDS = {
    'uzcard': {'label': 'Uzcard', 'number': '8600310416548592', 'holder': 'J*r**** D***a***ov'},
    'visa': {'label': 'Visa', 'number': '4195250052390109', 'holder': 'J*r**** D***a***ov'},
}

LOCAL_TEXTS = {
    'ru': {'main_menu':'🏠','edit_data_title':'Выберите, что хотите изменить:','choose_language':'Выберите язык:','select_country':'Выберите страну:','select_city':'Выберите город:','language_changed':'Язык обновлён.','location_changed':'Страна и город обновлены.','enter_number':'Пожалуйста, введите число.','enter_amount':'Введите сумму пополнения','choose_payment_card_country':'Выберите карту для перевода администратору:','send_receipt':'Отправьте скриншот/чек перевода.','payment_request_sent': MESSAGES['ru'].get('topup_request_sent','✅ Заявка на пополнение отправлена админу.'),'receipt_missing_photo':'Пожалуйста, отправьте именно фото чека.','approve_payment_btn':'✅ Подтвердить по указанной сумме','reject_payment_btn':'❌ Отклонить','edit_payment_amount_btn':'✏️ Ввести сумму вручную','enter_admin_topup_amount':'Введите сумму, на которую нужно пополнить баланс:','correct_amount_btn':'✅ Правильная сумма','card_holder_label':'Получатель','payment_approved_driver': MESSAGES['ru'].get('balance_topup_approved','✅ Пополнение баланса подтверждено.'),'payment_rejected_driver': MESSAGES['ru'].get('balance_topup_rejected','❌ Пополнение баланса отклонено.'),'payment_approved_admin':'Пополнение подтверждено.','payment_rejected_admin':'Пополнение отклонено.','driver_card_title':'Карта водителя','copy_hint':'Номер можно скопировать.','wallet_help':'Пополнение баланса выполняется через администратора после проверки перевода.','commission_due_label':'Комиссия сервиса','commission_paid_label':'Текущая комиссия','free_rides_left_label':'Льготные поездки','estimated_rides_label':'Режим сервиса','feedback_prompt':'Отправьте ваш отзыв или предложение одним сообщением. Можно текстом или голосовым.','feedback_sent':'✅ Спасибо! Ваше сообщение отправлено администрации.','feedback_title':'Новый отзыв или предложение','feedback_type':'Тип','feedback_text':'Текст','feedback_voice':'Голосовое сообщение','feedback_from':'Отправитель','feedback_kind_feedback':'Отзыв','feedback_kind_suggestion':'Предложение'},
    'uz': {'main_menu':'🏠','edit_data_title':'Nimani o‘zgartirmoqchisiz?','choose_language':'Tilni tanlang:','select_country':'Davlatni tanlang:','select_city':'Shaharni tanlang:','language_changed':'Til yangilandi.','location_changed':'Davlat va shahar yangilandi.','enter_number':'Iltimos, raqam kiriting.','enter_amount':'To‘ldirish summasini kiriting','choose_payment_card_country':'Adminga o‘tkazma uchun kartani tanlang:','send_receipt':'To‘lov cheki/skrinini yuboring.','payment_request_sent': MESSAGES['uz'].get('topup_request_sent','✅ Balansni to‘ldirish so‘rovi adminga yuborildi.'),'receipt_missing_photo':'Iltimos, aynan chek rasmini yuboring.','approve_payment_btn':'✅ Ko‘rsatilgan summa bilan tasdiqlash','reject_payment_btn':'❌ Rad etish','edit_payment_amount_btn':'✏️ Summani qo‘lda kiritish','enter_admin_topup_amount':'Balansni qaysi summaga to‘ldirish kerakligini kiriting:','correct_amount_btn':'✅ To‘g‘ri summa','card_holder_label':'Qabul qiluvchi','payment_approved_driver': MESSAGES['uz'].get('balance_topup_approved','✅ Balans to‘ldirildi va tasdiqlandi.'),'payment_rejected_driver': MESSAGES['uz'].get('balance_topup_rejected','❌ Balans to‘ldirish rad etildi.'),'payment_approved_admin':'To‘ldirish tasdiqlandi.','payment_rejected_admin':'To‘ldirish rad etildi.','driver_card_title':'Haydovchi kartasi','copy_hint':'Raqamni nusxalash mumkin.','wallet_help':'Balans administrator tomonidan to‘lov tekshirilgandan keyin to‘ldiriladi.','commission_due_label':'Xizmat komissiyasi','commission_paid_label':'Joriy komissiya','free_rides_left_label':'Imtiyozli safarlar','estimated_rides_label':'Xizmat rejimi','feedback_prompt':'Fikringiz yoki taklifingizni bitta xabar bilan yuboring. Matn yoki ovozli xabar bo‘lishi mumkin.','feedback_sent':'✅ Rahmat! Xabaringiz ma’muriyatga yuborildi.','feedback_title':'Yangi fikr yoki taklif','feedback_type':'Turi','feedback_text':'Matn','feedback_voice':'Ovozli xabar','feedback_from':'Yuboruvchi','feedback_kind_feedback':'Fikr','feedback_kind_suggestion':'Taklif'},
    'en': {'main_menu':'🏠','edit_data_title':'Choose what you want to edit:','choose_language':'Choose language:','select_country':'Select country:','select_city':'Select city:','language_changed':'Language updated.','location_changed':'Country and city updated.','enter_number':'Please enter a number.','enter_amount':'Enter top-up amount','choose_payment_card_country':'Choose the card for transfer to the admin:','send_receipt':'Send a screenshot/receipt of the transfer.','payment_request_sent': MESSAGES['en'].get('topup_request_sent','✅ Balance top-up request has been sent to the admin.'),'receipt_missing_photo':'Please send the receipt as a photo.','approve_payment_btn':'✅ Approve with this amount','reject_payment_btn':'❌ Reject','edit_payment_amount_btn':'✏️ Enter amount manually','enter_admin_topup_amount':'Enter the amount that should be credited to the balance:','correct_amount_btn':'✅ Correct amount','card_holder_label':'Recipient','payment_approved_driver': MESSAGES['en'].get('balance_topup_approved','✅ Balance top-up approved.'),'payment_rejected_driver': MESSAGES['en'].get('balance_topup_rejected','❌ Balance top-up rejected.'),'payment_approved_admin':'Top-up approved.','payment_rejected_admin':'Top-up rejected.','driver_card_title':'Driver card','copy_hint':'The number can be copied.','wallet_help':'Balance top-up is credited by the administrator after the payment is verified.','commission_due_label':'Service commission','commission_paid_label':'Current commission','free_rides_left_label':'Promo rides','estimated_rides_label':'Service mode','feedback_prompt':'Send your review or suggestion in one message. It can be text or a voice message.','feedback_sent':'✅ Thank you! Your message has been sent to the administration.','feedback_title':'New review or suggestion','feedback_type':'Type','feedback_text':'Text','feedback_voice':'Voice message','feedback_from':'Sender','feedback_kind_feedback':'Review','feedback_kind_suggestion':'Suggestion'},
    'ar': {'main_menu':'🏠','edit_data_title':'اختر ما تريد تعديله:','choose_language':'اختر اللغة:','select_country':'اختر الدولة:','select_city':'اختر المدينة:','language_changed':'تم تحديث اللغة.','location_changed':'تم تحديث الدولة والمدينة.','enter_number':'الرجاء إدخال رقم.','enter_amount':'أدخل مبلغ الشحن','choose_payment_card_country':'اختر البطاقة للتحويل إلى المسؤول:','send_receipt':'أرسل لقطة الشاشة/إيصال التحويل.','payment_request_sent': MESSAGES['ar'].get('topup_request_sent','✅ تم إرسال طلب شحن الرصيد إلى المسؤول.'),'receipt_missing_photo':'يرجى إرسال الإيصال على شكل صورة.','approve_payment_btn':'✅ تأكيد بالمبلغ الظاهر','reject_payment_btn':'❌ رفض','edit_payment_amount_btn':'✏️ إدخال المبلغ يدويًا','enter_admin_topup_amount':'أدخل المبلغ الذي يجب إضافةُه إلى الرصيد:','correct_amount_btn':'✅ المبلغ صحيح','card_holder_label':'المستفيد','payment_approved_driver': MESSAGES['ar'].get('balance_topup_approved','✅ تمت الموافقة على شحن الرصيد.'),'payment_rejected_driver': MESSAGES['ar'].get('balance_topup_rejected','❌ تم رفض شحن الرصيد.'),'payment_approved_admin':'تمت الموافقة على الشحن.','payment_rejected_admin':'تم رفض الشحن.','driver_card_title':'بطاقة السائق','copy_hint':'يمكن نسخ الرقم.','wallet_help':'يتم إضافة الرصيد من قِبل المسؤول بعد التحقق من التحويل.','commission_due_label':'عمولة الخدمة','commission_paid_label':'العمولة الحالية','free_rides_left_label':'الرحلات الترويجية','estimated_rides_label':'وضع الخدمة','feedback_prompt':'أرسل رأيك أو اقتراحك في رسالة واحدة. يمكن أن يكون نصًا أو رسالة صوتية.','feedback_sent':'✅ شكرًا لك! تم إرسال رسالتك إلى الإدارة.','feedback_title':'رأي أو اقتراح جديد','feedback_type':'النوع','feedback_text':'نص','feedback_voice':'رسالة صوتية','feedback_from':'المرسل','feedback_kind_feedback':'رأي','feedback_kind_suggestion':'اقتراح'},
}

def tr(lang: str, key: str, default: str = '') -> str:
    return LOCAL_TEXTS.get(lang, LOCAL_TEXTS['ru']).get(key) or MESSAGES.get(lang, MESSAGES['ru']).get(key) or MESSAGES['ru'].get(key) or default




def _profile_location_kb(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=tr(lang, 'share_location', '📍 Отправить текущую локацию'), request_location=True)], [types.KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_cancel', '❌ Cancel'))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _reverse_geocode_sync(lat: float, lng: float) -> dict:
    params = urlencode({'format': 'jsonv2', 'lat': f'{lat:.6f}', 'lon': f'{lng:.6f}'})
    req = Request(
        f'https://nominatim.openstreetmap.org/reverse?{params}',
        headers={'Accept': 'application/json', 'Accept-Language': 'ru,en,uz', 'User-Agent': 'IntaxiBot/1.0'}
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))


def _extract_geo_city(address: dict) -> str:
    for key in ('city', 'town', 'village', 'municipality', 'county', 'state_district'):
        value = (address.get(key) or '').strip()
        if value:
            return value
    return ''


def _country_code_from_address(address: dict) -> str:
    code = str(address.get('country_code') or '').lower()
    return code if code in {'uz', 'tr', 'sa'} else 'uz'



async def notify_admin_targets(bot: Bot, permission: str, *, text: str | None = None, photo: str | None = None, voice: str | None = None, caption: str | None = None, reply_markup=None, parse_mode: str | None = 'HTML'):
    admin_ids = await rq.get_admin_targets_by_permission(permission)
    for admin_id in admin_ids:
        try:
            if photo:
                await bot.send_photo(admin_id, photo=photo, caption=caption or text or '', reply_markup=reply_markup, parse_mode=parse_mode)
            elif voice:
                await bot.send_voice(admin_id, voice=voice, caption=caption or text or '', parse_mode=parse_mode)
            else:
                await bot.send_message(admin_id, text or caption or '', reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            pass
def is_driver_mode(user, vehicle=None):
    if not user.is_verified:
        return False
    if vehicle is None:
        return (user.active_role or 'driver') != 'passenger'
    return bool(vehicle) and (user.active_role or 'driver') != 'passenger'

for _lang, _value in {
    'ru': {'share_location': '📍 Отправить текущую локацию', 'location_detected': 'Определено по локации', 'detected_address': 'Определённый адрес', 'detected_coords': 'Координаты'},
    'uz': {'share_location': '📍 Joriy lokatsiyani yuborish', 'location_detected': 'Lokatsiya bo‘yicha aniqlandi', 'detected_address': 'Aniqlangan manzil', 'detected_coords': 'Koordinatalar'},
    'en': {'share_location': '📍 Send current location', 'location_detected': 'Detected from location', 'detected_address': 'Detected address', 'detected_coords': 'Coordinates'},
    'ar': {'share_location': '📍 إرسال الموقع الحالي', 'location_detected': 'تم التحديد من الموقع', 'detected_address': 'العنوان المحدد', 'detected_coords': 'الإحداثيات'},
}.items():
    LOCAL_TEXTS.setdefault(_lang, {}).update(_value)


class DepositMoney(StatesGroup):
    amount = State()

class PaymentReceiptFlow(StatesGroup):
    receipt = State()

class AdminPaymentAdjustFlow(StatesGroup):
    amount = State()

class EditProfile(StatesGroup):
    language = State()
    country = State()
    region = State()
    city = State()

class FeedbackFlow(StatesGroup):
    kind = State()
    content = State()

@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_profile') for l in MESSAGES))
async def show_profile(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    m = MESSAGES[lang]
    currency = m.get('currencies', {}).get(user.country, 'USD')
    async with async_session() as session:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
    display_country = m.get('countries', {}).get(user.country, user.country)
    username_line = f"@{user.username}" if user.username else "-"
    status_text = (
        f"<b>{user.full_name}</b>\n"
        f"ID: <code>{user.tg_id}</code>\n"
        f"Username: {username_line}\n"
        f"{m.get('language', 'Language')}: {lang.upper()}\n"
        f"{display_country}, {user.city}\n"
        f"{m.get('balance_label', 'Баланс')}: {user.balance or 0.0} {currency}\n"
    )
    show_driver_section = bool(vehicle) and (user.active_role or "passenger") != "passenger"
    if show_driver_section:
        verif_label = m.get('verified') if user.is_verified else m.get('on_moderation')
        verif = ("✅ " if user.is_verified else "⏳ ") + verif_label
        active_modes = []
        if getattr(vehicle, 'accepts_class4', True):
            active_modes.append(m.get('class4_short', 'До 4 мест'))
        if getattr(vehicle, 'accepts_class7', False):
            active_modes.append(m.get('class7_short', 'До 7 мест'))
        status_text += (
            f"\n🚖 <b>{m.get('driver_status')}:</b>\n"
            f"🚗 {vehicle.brand} {vehicle.model}\n"
            f"🔢 {vehicle.plate}\n"
            + (f"🎨 {m.get('color_label', 'Цвет')}: {vehicle.color}\n" if getattr(vehicle, 'color', None) else "")
            + f"👥 {m.get('vehicle_class_label', 'Класс машины')}: {m.get('class7_short') if getattr(vehicle, 'vehicle_class', 'class4') == 'class7' else m.get('class4_short')}\n"
            + f"📦 {m.get('supported_classes_label', 'Может принимать')}: {', '.join(active_modes)}\n"
            + f"🔄 {m.get('current_mode_label', 'Текущий режим')}: {m.get('mode_passenger_label') if (user.active_role or 'driver') == 'passenger' else m.get('mode_driver_label')}\n"
            + f"📊 {m.get('status')}: {verif}\n"
            + f"⭐ {user.rating or 0.0}\n"
            + f"💳 <b>{tr(lang, 'driver_card_title')}:</b> {user.driver_card_country or '-'} | <code>{user.driver_card_number or '-'}</code>\n"
            + f"📋 {tr(lang, 'copy_hint')}"
        )
    else:
        status_text += f"\n🎭 {m.get('user_role')}: {m.get('role_passenger')}"
    donate_lines = [
        os.getenv('NEXT_PUBLIC_DONATE_FIAT_UZ', '').strip(),
        os.getenv('NEXT_PUBLIC_DONATE_BTC', '').strip(),
        os.getenv('NEXT_PUBLIC_DONATE_ETH', '').strip(),
        os.getenv('NEXT_PUBLIC_DONATE_SOL', '').strip(),
    ]
    donate_lines = [line for line in donate_lines if line]
    if donate_lines:
        status_text += '\n\n🤝 Поддержка проекта:\n' + '\n'.join(f'<code>{line}</code>' for line in donate_lines[:4])
    await message.answer(ayah_header(lang) + status_text, reply_markup=kb.profile_menu(lang, show_become_driver=(not bool(vehicle) and not user.is_verified)), parse_mode='HTML')

@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_feedback', '💬 Отзывы и предложения') for l in MESSAGES))
async def feedback_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(lang, 'feedback_kind_feedback'), callback_data='feedback_kind_feedback')
    builder.button(text=tr(lang, 'feedback_kind_suggestion'), callback_data='feedback_kind_suggestion')
    builder.adjust(1)
    await message.answer(tr(lang, 'feedback_prompt'), reply_markup=builder.as_markup())
    await state.set_state(FeedbackFlow.kind)


@router.callback_query(F.data.startswith('feedback_kind_'), FeedbackFlow.kind)
async def feedback_kind_selected(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    kind = callback.data.split('feedback_kind_', 1)[1]
    await state.update_data(feedback_kind=kind)
    await state.set_state(FeedbackFlow.content)
    await callback.message.answer(tr(lang, 'feedback_prompt'))
    await callback.answer()


@router.message(FeedbackFlow.content, F.voice)
async def feedback_voice_received(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    kind = data.get('feedback_kind', 'feedback')
    entry = await rq.create_feedback_entry(user.tg_id, kind, 'voice', file_id=message.voice.file_id)
    await state.clear()
    caption = (
        f"💬 <b>{tr('ru', 'feedback_title')}</b>\n\n"
        f"{tr('ru', 'feedback_type')}: {tr('ru', 'feedback_kind_' + kind)}\n"
        f"{tr('ru', 'feedback_from')}: {user.full_name}\n"
        f"@{user.username} | ID: {user.tg_id}\n"
        f"#feedback_{entry.id if entry else 'new'}"
    )
    await notify_admin_targets(bot, 'moderation', voice=message.voice.file_id, caption=caption, parse_mode='HTML')
    await message.answer(tr(lang, 'feedback_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.message(FeedbackFlow.content)
async def feedback_text_received(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    kind = data.get('feedback_kind', 'feedback')
    entry = await rq.create_feedback_entry(user.tg_id, kind, 'text', text_value=message.text or '')
    await state.clear()
    admin_text = (
        f"💬 <b>{tr('ru', 'feedback_title')}</b>\n\n"
        f"{tr('ru', 'feedback_type')}: {tr('ru', 'feedback_kind_' + kind)}\n"
        f"{tr('ru', 'feedback_from')}: {user.full_name}\n"
        f"@{user.username} | ID: {user.tg_id}\n\n"
        f"{message.html_text or message.text}\n\n"
        f"#feedback_{entry.id if entry else 'new'}"
    )
    await notify_admin_targets(bot, 'moderation', text=admin_text, parse_mode='HTML')
    await message.answer(tr(lang, 'feedback_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_wallet', '💰 Баланс') for l in MESSAGES))
async def show_wallet(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    m = MESSAGES[lang]
    currency = m.get('currencies', {}).get(user.country, 'USD')
    builder = InlineKeyboardBuilder()
    builder.button(text='➕ ' + m.get('deposit_btn', 'Top up'), callback_data='deposit_start')
    builder.adjust(1)
    text = f"💳 <b>{m.get('wallet_title', 'Wallet')}</b>\n\n💰 {m.get('current_balance', 'Current balance')}: {user.balance or 0.0} {currency}\n"
    if user.is_verified:
        text += f"💸 {tr(lang, 'commission_due_label')}: 0%\n✅ {tr(lang, 'commission_paid_label')}: 0%\n🎁 {tr(lang, 'free_rides_left_label')}: 0\n🧮 {tr(lang, 'estimated_rides_label')}: 0%\n"
    if user.driver_card_number:
        text += f"\n💳 <b>{tr(lang, 'driver_card_title')}:</b> {user.driver_card_country or '-'} | <code>{user.driver_card_number}</code>\n📋 {tr(lang, 'copy_hint')}\n"
    text += f"\n{tr(lang, 'wallet_help')}"
    await message.answer(ayah_header(lang) + text, reply_markup=builder.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == 'deposit_start')
async def deposit_start(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    lang = user.language or 'ru'
    currency = MESSAGES[lang].get('currencies', {}).get(user.country, 'USD')
    await callback.message.answer(f"{tr(lang, 'enter_amount')} ({currency}):")
    await state.set_state(DepositMoney.amount)
    await callback.answer()

@router.message(DepositMoney.amount)
async def deposit_amount(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    try:
        amount = float(message.text.replace(',', '.'))
    except Exception:
        await message.answer(tr(lang, 'enter_number'))
        return
    await state.update_data(topup_amount=amount)
    await message.answer(tr(lang, 'choose_payment_card_country'), reply_markup=kb.payment_cards_kb(lang))

@router.callback_query(F.data.startswith('paycard_'))
async def choose_pay_card(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    lang = user.language or 'ru'
    card_country = callback.data.split('_', 1)[1]
    card_data = ADMIN_RECEIVING_CARDS.get(card_country)
    if not card_data:
        await callback.answer(show_alert=True)
        return
    await state.update_data(admin_card_country=card_country, admin_card_number=card_data['number'])
    await state.set_state(PaymentReceiptFlow.receipt)
    await callback.message.answer(f"{card_data['label']}\n<code>{card_data['number']}</code>\n{tr(lang, 'card_holder_label')}: <b>{card_data['holder']}</b>\n\n{tr(lang, 'send_receipt')}", parse_mode='HTML')
    await callback.answer()

@router.message(PaymentReceiptFlow.receipt, F.photo)
async def receive_payment_receipt(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    data = await state.get_data()
    amount = float(data.get('topup_amount', 0) or 0)
    payment_request = await rq.create_driver_payment_request(
        driver_tg_id=message.from_user.id,
        card_country=data.get('admin_card_country'),
        admin_card_number=data.get('admin_card_number'),
        amount=amount,
        receipt_file_id=message.photo[-1].file_id,
    )
    await state.clear()
    admin_lang = 'ru'
    await notify_admin_targets(
        bot,
        'finance',
        photo=message.photo[-1].file_id,
        caption=(
            f"{tr(admin_lang, 'admin_receipt_new')}\n"
            f"{tr(admin_lang, 'user_label')}: {user.full_name}\n"
            f"TG ID: {user.tg_id}\n"
            f"{tr(admin_lang, 'amount_label')}: {amount}\n"
            f"{tr(admin_lang, 'card_label')}: {data.get('admin_card_country', '').upper()} | {data.get('admin_card_number', '-')}\n"
            f"{tr(admin_lang, 'card_holder_label')}: {ADMIN_RECEIVING_CARDS.get(data.get('admin_card_country'), {}).get('holder', '-')}"
        ),
        reply_markup=kb.payment_admin_decision_kb(
            payment_request.id,
            tr(admin_lang, 'correct_amount_btn'),
            tr(admin_lang, 'reject_payment_btn'),
            tr(admin_lang, 'edit_payment_amount_btn'),
        ),
        parse_mode='HTML',
    )
    await message.answer(tr(lang, 'payment_request_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))

@router.message(PaymentReceiptFlow.receipt)
async def receive_payment_receipt_wrong_type(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    await message.answer(tr(user.language or 'ru', 'receipt_missing_photo'))

@router.callback_query(F.data.startswith('editpay_'))
async def edit_payment_amount_start(callback: types.CallbackQuery, state: FSMContext):
    if not await rq.admin_has_permission(callback.from_user.id, 'finance'):
        await callback.answer()
        return
    request_id = int(callback.data.split('_', 1)[1])
    await state.clear()
    await state.update_data(payment_request_id=request_id)
    await state.set_state(AdminPaymentAdjustFlow.amount)
    await callback.message.answer(tr('ru', 'enter_admin_topup_amount'))
    await callback.answer()


@router.message(AdminPaymentAdjustFlow.amount)
async def edit_payment_amount_finish(message: types.Message, state: FSMContext, bot: Bot):
    if not await rq.admin_has_permission(message.from_user.id, 'finance'):
        await state.clear()
        return
    data = await state.get_data()
    request_id = data.get('payment_request_id')
    try:
        amount = float(str(message.text).replace(',', '.'))
    except Exception:
        await message.answer(tr('ru', 'enter_number'))
        return
    updated = await rq.update_driver_payment_request_amount(request_id, amount)
    await state.clear()
    if not updated:
        await message.answer(tr('ru', 'payment_rejected_admin'))
        return
    result = await rq.approve_driver_payment_request(request_id)
    if not result:
        await message.answer(tr('ru', 'payment_rejected_admin'))
        return
    _, target_user = result
    lang = target_user.language or 'ru'
    await bot.send_message(target_user.tg_id, tr(lang, 'payment_approved_driver'), reply_markup=kb.main_menu(lang, user_id=target_user.tg_id, as_user=True, is_driver_mode=bool(target_user.is_verified and (target_user.active_role or 'driver') != 'passenger')))
    await message.answer(tr('ru', 'payment_approved_admin') + f' ({amount})')


@router.callback_query(F.data.startswith('approvepay_'))
async def approve_payment(callback: types.CallbackQuery, bot: Bot):
    if not await rq.admin_has_permission(callback.from_user.id, 'finance'):
        await callback.answer()
        return
    request_id = int(callback.data.split('_', 1)[1])
    result = await rq.approve_driver_payment_request(request_id)
    if not result:
        await callback.answer(show_alert=True)
        return
    _, target_user = result
    lang = target_user.language or 'ru'
    await bot.send_message(target_user.tg_id, tr(lang, 'payment_approved_driver'), reply_markup=kb.main_menu(lang, user_id=target_user.tg_id, as_user=True, is_driver_mode=bool(target_user.is_verified and (target_user.active_role or 'driver') != 'passenger')))
    try:
        await callback.message.edit_caption(caption=(callback.message.caption or '') + '\n\n✅ APPROVED')
    except Exception:
        pass
    await callback.message.answer(tr('ru', 'payment_approved_admin'))
    await callback.answer('OK')

@router.callback_query(F.data.startswith('rejectpay_'))
async def reject_payment(callback: types.CallbackQuery, bot: Bot):
    if not await rq.admin_has_permission(callback.from_user.id, 'finance'):
        await callback.answer()
        return
    request_id = int(callback.data.split('_', 1)[1])
    result = await rq.reject_driver_payment_request(request_id)
    if not result:
        await callback.answer(show_alert=True)
        return
    _, target_user = result
    lang = target_user.language or 'ru'
    await bot.send_message(target_user.tg_id, tr(lang, 'payment_rejected_driver'), reply_markup=kb.main_menu(lang, user_id=target_user.tg_id, as_user=True, is_driver_mode=bool(target_user.is_verified and (target_user.active_role or 'driver') != 'passenger')))
    try:
        await callback.message.edit_caption(caption=(callback.message.caption or '') + '\n\n❌ REJECTED')
    except Exception:
        pass
    await callback.message.answer(tr('ru', 'payment_rejected_admin'))
    await callback.answer('OK')

@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_edit_data'] for x in kb.LOCAL_DEFAULTS])
async def open_edit_data_menu(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    async with async_session() as session:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
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
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    await state.clear()
    await state.set_state(EditProfile.language)
    await message.answer(tr(lang, 'choose_language'), reply_markup=kb.language_kb)

@router.message(EditProfile.language)
async def change_language_finish(message: types.Message, state: FSMContext):
    lang_map = {'🇷🇺 Русский':'ru','🇺🇿 O\'zbekcha':'uz','🇬🇧 English':'en','🇸🇦 العربية':'ar'}
    lang = lang_map.get(message.text)
    if not lang:
        return
    await rq.update_user_language(message.from_user.id, lang)
    await state.clear()
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    await message.answer(tr(lang, 'language_changed'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))

@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_change_location'] for x in kb.LOCAL_DEFAULTS])
async def change_location_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
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
        country_code = _country_code_from_address(address)
        city = _extract_geo_city(address) or user.city or f'{lat}, {lng}'
        await rq.update_user_country_city(message.from_user.id, country_code, city)
        await state.clear()
        detected_address = data.get('display_name') or city
        detected_coords = f'{lat}, {lng}'
        await message.answer(
            f"{tr(lang, 'location_changed')}\n\n{tr(lang, 'detected_address')}: {detected_address}\n{tr(lang, 'detected_coords')}: <code>{detected_coords}</code>",
            parse_mode='HTML',
            reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user))
        )
    except Exception:
        await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.callback_query(F.data.startswith('editcountry_'), EditProfile.country)
async def edit_country_pick(callback: types.CallbackQuery, state: FSMContext):
    country_code = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data['language']
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
    lang = data['language']
    await state.update_data(region=region_key)
    builder = build_localities_keyboard(region_key, lang, 'edituzcity_')
    await callback.message.edit_text(tr(lang, 'select_district_city'), reply_markup=builder.as_markup())
    await state.set_state(EditProfile.city)
    await callback.answer()

@router.callback_query(F.data.startswith('editcity_'), EditProfile.city)
async def edit_city_pick(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('_', 1)[1]
    data = await state.get_data()
    lang = data['language']
    await rq.update_user_country_city(callback.from_user.id, data['country'], city)
    await state.clear()
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    await callback.message.answer(tr(lang, 'location_changed'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
    await callback.answer()

@router.callback_query(F.data.startswith('edituzcity_'), EditProfile.city)
async def edit_uz_city_pick(callback: types.CallbackQuery, state: FSMContext):
    payload = callback.data.split('_', 1)[1]
    region_key, idx_raw = payload.split(':', 1)
    data = await state.get_data()
    lang = data['language']
    locality = get_locality_by_index(region_key, lang, int(idx_raw))
    city_value = format_uz_location(region_key, locality, lang)
    await rq.update_user_country_city(callback.from_user.id, data['country'], city_value)
    await state.clear()
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    await callback.message.answer(tr(lang, 'location_changed'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
    await callback.answer()

@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x]['btn_change_vehicle'] for x in kb.LOCAL_DEFAULTS])
async def change_vehicle_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    async with async_session() as session:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
    if not vehicle:
        return
    await rq.remove_vehicle_for_edit(message.from_user.id)
    await state.clear()
    await message.answer(MESSAGES[lang].get('moderation', 'Введите данные машины заново.'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
    await message.answer(MESSAGES[lang].get('become_driver'))

@router.message(lambda message: message.text in [kb.LOCAL_DEFAULTS[x].get('btn_toggle_small_orders_on') for x in kb.LOCAL_DEFAULTS] + [kb.LOCAL_DEFAULTS[x].get('btn_toggle_small_orders_off') for x in kb.LOCAL_DEFAULTS])
async def toggle_small_orders_mode(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    vehicle = await rq.toggle_driver_accepts_class4(user.tg_id)
    if not vehicle:
        await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
        return
    key = 'toggle_small_orders_enabled' if vehicle.accepts_class4 else 'toggle_small_orders_disabled'
    await message.answer(MESSAGES[lang].get(key, key), reply_markup=kb.edit_data_menu(lang, is_driver=True, show_become_driver=False, show_class4_toggle=True, class4_enabled=vehicle.accepts_class4, show_role_toggle=True, active_role=(user.active_role or 'driver')))

@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_switch_role_to_passenger') for l in MESSAGES) or any(message.text == MESSAGES[l].get('btn_switch_role_to_driver') for l in MESSAGES))
async def toggle_driver_role_mode(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    async with async_session() as session:
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
    if not (user.is_verified and vehicle):
        await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
        return
    new_role = 'passenger' if (user.active_role or 'driver') != 'passenger' else 'driver'
    user = await rq.set_user_active_role(user.tg_id, new_role)
    msg_key = 'role_switched_to_passenger' if new_role == 'passenger' else 'role_switched_to_driver'
    await message.answer(MESSAGES[lang].get(msg_key, msg_key), reply_markup=kb.edit_data_menu(lang, is_driver=True, show_become_driver=False, show_class4_toggle=(getattr(vehicle, 'vehicle_class', 'class4')=='class7'), class4_enabled=bool(getattr(vehicle, 'accepts_class4', True)), show_role_toggle=True, active_role=new_role))

@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_back') for l in MESSAGES))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    lang = user.language or 'ru'
    await state.clear()
    await message.answer(tr(lang, 'main_menu'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
