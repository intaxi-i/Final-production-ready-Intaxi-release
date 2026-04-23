import os
import sqlite3
from pathlib import Path

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.strings import MESSAGES
from app.miniapp_routes import city_main_url, intercity_main_url, profile_url, wallet_url, current_trip_url


LOCAL_DEFAULTS = {
    'ru': {
        'btn_intercity': '🛣 Межгород',
        'btn_publish_route': '🚘 Опубликовать маршрут',
        'btn_my_routes': '📋 Мои маршруты',
        'btn_finish_route': '🛑 Снять маршрут',
        'btn_from_my_city': '📤 Из моего города',
        'btn_to_my_city': '📥 В мой город',
        'btn_skip': '⏭ Пропустить',
        'btn_edit_order': '✏️ Скорректировать заказ',
        'btn_cancel_search': '🛑 Отменить поиск',
        'btn_back_inline': '⬅️ Назад',
        'btn_cancel_inline': '❌ Отмена',
        'btn_edit_data': '⚙️ Изменить данные',
        'btn_change_language': '🌐 Сменить язык',
        'btn_change_location': '🌍 Сменить страну и город',
        'btn_change_vehicle': '🚗 Изменить данные авто',
        'btn_change_price': '💰 Сменить цену',
        'btn_change_time': '⏰ Сменить время',
        'btn_change_stop': '📍 Указать промежуточную точку',
        'btn_change_pickup_note': '📝 Указать ориентир откуда',
        'btn_change_destination_note': '📝 Указать ориентир куда',
        'btn_offer_price': '💰 Предложить свою цену',
        'btn_accept_price': '✅ Принять цену',
        'btn_reject_price': '❌ Отклонить',
        'btn_available_orders': '📋 Доступные предложения по межгороду',
        'btn_pay_commission': '💳 Баланс и пополнение',
        'btn_current_order': '📌 Текущий заказ',
        'btn_pay_trip_balance': '💳 Оплатить из баланса',
        'btn_toggle_small_orders_on': '🚫 Отключить 4-местные заказы',
        'btn_toggle_small_orders_off': '✅ Включить 4-местные заказы',
        'btn_go_trip': '🚘 Поехать',
        'btn_complaint': '⚠️ Жалоба',
        'btn_feedback': '💬 Отзывы и предложения',
        'btn_mini_city': '🏙 Город',
        'btn_mini_intercity': '🛣 Межгород',
        'btn_mini_profile': '👤 Профиль',
        'btn_mini_wallet': '💰 Баланс',
    },
    'uz': {
        'btn_intercity': '🛣 Shaharlararo',
        'btn_publish_route': '🚘 Yo‘nalish joylash',
        'btn_my_routes': '📋 Mening yo‘nalishlarim',
        'btn_finish_route': '🛑 Yo‘nalishni yopish',
        'btn_from_my_city': '📤 Mening shahrimdan',
        'btn_to_my_city': '📥 Mening shahrimga',
        'btn_skip': '⏭ O‘tkazib yuborish',
        'btn_edit_order': '✏️ Buyurtmani tuzatish',
        'btn_cancel_search': '🛑 Qidiruvni bekor qilish',
        'btn_back_inline': '⬅️ Orqaga',
        'btn_cancel_inline': '❌ Bekor qilish',
        'btn_edit_data': '⚙️ Ma’lumotlarni o‘zgartirish',
        'btn_change_language': '🌐 Tilni o‘zgartirish',
        'btn_change_location': '🌍 Davlat va shaharni o‘zgartirish',
        'btn_change_vehicle': '🚗 Avto ma’lumotlarini o‘zgartirish',
        'btn_change_price': '💰 Narxni o‘zgartirish',
        'btn_change_time': '⏰ Vaqtni o‘zgartirish',
        'btn_change_stop': '📍 Oraliq nuqtani ko‘rsatish',
        'btn_change_pickup_note': '📝 Qayerdan mo‘ljal',
        'btn_change_destination_note': '📝 Qayerga mo‘ljal',
        'btn_offer_price': '💰 O‘z narxini taklif qilish',
        'btn_accept_price': '✅ Narxni qabul qilish',
        'btn_reject_price': '❌ Rad etish',
        'btn_available_orders': '📋 Shaharlararo takliflar',
        'btn_pay_commission': '💳 Balans va to‘ldirish',
        'btn_current_order': '📌 Joriy buyurtma',
        'btn_pay_trip_balance': '💳 Balansdan to‘lash',
        'btn_toggle_small_orders_on': '🚫 4 o‘rinli buyurtmalarni o‘chirish',
        'btn_toggle_small_orders_off': '✅ 4 o‘rinli buyurtmalarni yoqish',
        'btn_go_trip': '🚘 Yo‘lga chiqish',
        'btn_complaint': '⚠️ Shikoyat',
        'btn_feedback': '💬 Fikr va takliflar',
        'btn_mini_city': '🏙 Shahar',
        'btn_mini_intercity': '🛣 Shaharlararo',
        'btn_mini_profile': '👤 Profil',
        'btn_mini_wallet': '💰 Balans',
    },
    'en': {
        'btn_intercity': '🛣 Intercity',
        'btn_publish_route': '🚘 Publish route',
        'btn_my_routes': '📋 My routes',
        'btn_finish_route': '🛑 Close route',
        'btn_from_my_city': '📤 From my city',
        'btn_to_my_city': '📥 To my city',
        'btn_skip': '⏭ Skip',
        'btn_edit_order': '✏️ Edit order',
        'btn_cancel_search': '🛑 Cancel search',
        'btn_back_inline': '⬅️ Back',
        'btn_cancel_inline': '❌ Cancel',
        'btn_edit_data': '⚙️ Edit data',
        'btn_change_language': '🌐 Change language',
        'btn_change_location': '🌍 Change country and city',
        'btn_change_vehicle': '🚗 Change vehicle data',
        'btn_change_price': '💰 Change price',
        'btn_change_time': '⏰ Change time',
        'btn_change_stop': '📍 Set intermediate stop',
        'btn_change_pickup_note': '📝 Pickup hint',
        'btn_change_destination_note': '📝 Destination hint',
        'btn_offer_price': '💰 Offer your price',
        'btn_accept_price': '✅ Accept price',
        'btn_reject_price': '❌ Reject',
        'btn_available_orders': '📋 Available intercity offers',
        'btn_pay_commission': '💳 Balance and top up',
        'btn_current_order': '📌 Current order',
        'btn_pay_trip_balance': '💳 Pay from balance',
        'btn_toggle_small_orders_on': '🚫 Disable 4-seat orders',
        'btn_toggle_small_orders_off': '✅ Enable 4-seat orders',
        'btn_go_trip': '🚘 Start trip',
        'btn_complaint': '⚠️ Complaint',
        'btn_feedback': '💬 Reviews and suggestions',
        'btn_mini_city': '🏙 City',
        'btn_mini_intercity': '🛣 Intercity',
        'btn_mini_profile': '👤 Profile',
        'btn_mini_wallet': '💰 Wallet',
    },
    'ar': {
        'btn_intercity': '🛣 بين المدن',
        'btn_publish_route': '🚘 نشر المسار',
        'btn_my_routes': '📋 مساراتي',
        'btn_finish_route': '🛑 إغلاق المسار',
        'btn_from_my_city': '📤 من مدينتي',
        'btn_to_my_city': '📥 إلى مدينتي',
        'btn_skip': '⏭ تخطي',
        'btn_edit_order': '✏️ تعديل الطلب',
        'btn_cancel_search': '🛑 إلغاء البحث',
        'btn_back_inline': '⬅️ رجوع',
        'btn_cancel_inline': '❌ إلغاء',
        'btn_edit_data': '⚙️ تعديل البيانات',
        'btn_change_language': '🌐 تغيير اللغة',
        'btn_change_location': '🌍 تغيير الدولة والمدينة',
        'btn_change_vehicle': '🚗 تغيير بيانات السيارة',
        'btn_change_price': '💰 تغيير السعر',
        'btn_change_time': '⏰ تغيير الوقت',
        'btn_change_stop': '📍 تحديد نقطة توقف',
        'btn_change_pickup_note': '📝 وصف نقطة الانطلاق',
        'btn_change_destination_note': '📝 وصف نقطة الوصول',
        'btn_offer_price': '💰 اقترح سعرك',
        'btn_accept_price': '✅ قبول السعر',
        'btn_reject_price': '❌ رفض',
        'btn_available_orders': '📋 العروض المتاحة بين المدن',
        'btn_pay_commission': '💳 الرصيد والتعبئة',
        'btn_current_order': '📌 الطلب الحالي',
        'btn_pay_trip_balance': '💳 الدفع من الرصيد',
        'btn_toggle_small_orders_on': '🚫 تعطيل طلبات 4 مقاعد',
        'btn_toggle_small_orders_off': '✅ تفعيل طلبات 4 مقاعد',
        'btn_go_trip': '🚘 انطلق',
        'btn_complaint': '⚠️ شكوى',
        'btn_feedback': '💬 الآراء والاقتراحات',
        'btn_mini_city': '🏙 المدينة',
        'btn_mini_intercity': '🛣 بين المدن',
        'btn_mini_profile': '👤 الملف الشخصي',
        'btn_mini_wallet': '💰 الرصيد',
    },
}


def _t(lang: str, key: str, default: str = ''):
    return LOCAL_DEFAULTS.get(lang, LOCAL_DEFAULTS['ru']).get(key, default)


def mini_app_base_url() -> str:
    return os.getenv('MINI_APP_URL', 'https://app.intaxi.best').rstrip('/')


def mini_app_url(path: str = '/') -> str:
    base = mini_app_base_url()
    if not path:
        return base
    normalized = path if path.startswith('/') else f'/{path}'
    return f'{base}{normalized}'


def mini_app_web_app(path: str = '/') -> types.WebAppInfo:
    return types.WebAppInfo(url=mini_app_url(path))


language_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🇷🇺 Русский'), KeyboardButton(text="🇺🇿 O'zbekcha")],
        [KeyboardButton(text='🇬🇧 English'), KeyboardButton(text='🇸🇦 العربية')],
    ],
    resize_keyboard=True,
)




def _db_admin_role(user_id):
    if not user_id:
        return None
    roles = set()
    try:
        database_url = os.getenv('DATABASE_URL', '').strip()
        db_path = None
        if database_url.startswith('sqlite'):
            raw = database_url.split('///', 1)[-1].strip()
            if raw:
                db_path = Path(raw)
        if db_path is None:
            db_path = Path(__file__).resolve().parents[2] / 'db.sqlite3'
        if not db_path.exists():
            fallback = Path.cwd() / 'db.sqlite3'
            if fallback.exists():
                db_path = fallback
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            try:
                rows = conn.execute("SELECT role FROM admin_roles WHERE tg_id=? AND is_active=1", (int(user_id),)).fetchall()
                roles = {row[0] for row in rows}
            finally:
                conn.close()
    except Exception:
        roles = set()
    if not roles:
        raw_superadmins = os.getenv('SUPERADMIN_IDS', '').strip()
        if str(user_id) in {part.strip() for part in raw_superadmins.split(',') if part.strip()}:
            roles.add('superadmin')
    for role in ('superadmin', 'admin', 'moderator', 'finance'):
        if role in roles:
            return role
    return None


def _db_admin_flag(user_id):
    return bool(_db_admin_role(user_id))


def intercity_main_text(lang, is_driver_mode: bool = False):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    if is_driver_mode:
        return m.get('btn_intercity_driver', _t(lang, 'btn_intercity'))
    return m.get('btn_intercity_passenger', _t(lang, 'btn_intercity'))

def main_menu(lang, user_id=None, as_user=False, is_driver_mode: bool = False, is_admin: bool | None = None):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    admin_flag = _db_admin_flag(user_id) if is_admin is None else bool(is_admin)
    if admin_flag and not as_user:
        return admin_main_kb(lang, user_id=user_id)

    keyboard = [
        [KeyboardButton(text=m['btn_fast_order']), KeyboardButton(text=intercity_main_text(lang, is_driver_mode))],
        [KeyboardButton(text=_t(lang, 'btn_current_order'))],
        [KeyboardButton(text=m.get('btn_profile', _t(lang, 'btn_mini_profile'))), KeyboardButton(text=m.get('btn_wallet', _t(lang, 'btn_mini_wallet')))],
        [KeyboardButton(text=_t(lang, 'btn_feedback'))],
    ]

    if admin_flag and as_user:
        admin_panel_labels = {
            'ru': '🛡 Админ-панель',
            'uz': '🛡 Admin paneli',
            'en': '🛡 Admin panel',
            'ar': '🛡 لوحة الإدارة',
        }
        keyboard.append([KeyboardButton(text=admin_panel_labels.get(lang, admin_panel_labels['ru']))])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def admin_main_kb(lang='ru', user_id=None):
    labels = {
        'dashboard': '📊 Dashboard',
        'users': '👥 Пользователи',
        'drivers': '🚕 Водители',
        'finance': '💳 Финансы',
        'orders': '🧾 Заказы',
        'moderation': '🛎 Модерация',
        'broadcast': '📢 Рассылка',
        'payments': '💳 Пополнения',
        'lookup': '🔎 Пользователь по ID',
        'feedback': '💬 Отзывы',
        'complaints': '⚠️ Жалобы',
        'user_mode': '👤 Режим пользователя',
        'admins': '🛡 Админы',
    }
    role = _db_admin_role(user_id)
    permissions = {
        'superadmin': ['dashboard', 'users', 'drivers', 'finance', 'orders', 'moderation', 'payments', 'lookup', 'feedback', 'complaints', 'broadcast', 'admins'],
        'admin': ['dashboard', 'users', 'drivers', 'orders', 'moderation', 'payments', 'lookup', 'feedback', 'complaints'],
        'moderator': ['dashboard', 'drivers', 'moderation', 'feedback', 'complaints'],
        'finance': ['dashboard', 'finance', 'payments', 'lookup'],
    }.get(role, ['dashboard'])
    rows = []
    current = []
    for key in permissions:
        current.append(KeyboardButton(text=labels[key]))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append([KeyboardButton(text=labels['user_mode'])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)




def profile_menu(lang, show_become_driver=False):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    keyboard = [
        [KeyboardButton(text=m.get('btn_wallet', '💰 Баланс'))],
        [KeyboardButton(text=_t(lang, 'btn_edit_data'))],
    ]
    if show_become_driver:
        keyboard.append([KeyboardButton(text=m.get('btn_become_driver', '🚕 Стать водителем'))])
    keyboard.append([KeyboardButton(text=LOCAL_DEFAULTS.get(lang, LOCAL_DEFAULTS['ru']).get('btn_feedback', '💬 Отзывы и предложения'))])
    keyboard.append([KeyboardButton(text=m.get('btn_back', '⬅️ Назад'))])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
def edit_data_menu(lang, is_driver=False, show_become_driver=False, show_class4_toggle=False, class4_enabled=False, show_role_toggle=False, active_role='driver'):
    keyboard = [
        [KeyboardButton(text=_t(lang, 'btn_change_language'))],
        [KeyboardButton(text=_t(lang, 'btn_change_location'))],
    ]
    if is_driver:
        keyboard.append([KeyboardButton(text=_t(lang, 'btn_change_vehicle'))])
        if show_class4_toggle:
            toggle_key = 'btn_toggle_small_orders_on' if class4_enabled else 'btn_toggle_small_orders_off'
            keyboard.append([KeyboardButton(text=_t(lang, toggle_key))])
        if show_role_toggle:
            role_key = 'btn_switch_role_to_passenger' if active_role != 'passenger' else 'btn_switch_role_to_driver'
            keyboard.append([KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru']).get(role_key, role_key))])
    if show_become_driver:
        keyboard.append([KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru'])['become_driver'])])
    keyboard.append([KeyboardButton(text=MESSAGES.get(lang, MESSAGES['ru'])['btn_back'])])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def location_kb(lang):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=m['btn_send_loc'], request_location=True)],
            [KeyboardButton(text=m['btn_cancel'])],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def destination_input_kb(lang):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=m['btn_cancel'])]], resize_keyboard=True, one_time_keyboard=True)


def time_selection_kb(lang):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=m['time_now'])], [KeyboardButton(text=m['btn_cancel'])]], resize_keyboard=True)


def car_types_kb(lang):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    buttons = [[KeyboardButton(text=car_type)] for car_type in m['car_types']]
    buttons.append([KeyboardButton(text=m['btn_cancel'])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def driver_active_order_kb(lang, order_id: int):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    builder = InlineKeyboardBuilder()
    builder.button(text=m.get('btn_arrived', '📍 Arrived'), callback_data=f'arrived_{order_id}')
    builder.button(text=m['btn_finish_order'], callback_data=f'finish_{order_id}')
    builder.button(text=_t(lang, 'btn_complaint'), callback_data=f'compl_city_driver_{order_id}')
    builder.button(text=m['btn_cancel_order'], callback_data=f'cancl_{order_id}')
    return builder.adjust(1).as_markup()


def passenger_active_order_kb(lang, order_id: int, show_pay: bool = True):
    builder = InlineKeyboardBuilder()
    if show_pay:
        builder.button(text=_t(lang, 'btn_pay_trip_balance'), callback_data=f'payorder_{order_id}')
    builder.button(text=_t(lang, 'btn_complaint'), callback_data=f'compl_city_passenger_{order_id}')
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru'])['btn_cancel_order'], callback_data=f'cancl_{order_id}')
    return builder.adjust(1).as_markup()




def passenger_arrived_kb(lang, order_id: int):
    m = MESSAGES.get(lang, MESSAGES['ru'])
    builder = InlineKeyboardBuilder()
    builder.button(text=m.get('btn_coming', '🚶 Coming'), callback_data=f'coming_{order_id}')
    return builder.adjust(1).as_markup()

def rating_kb(lang, rated_user_id: int):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f'{i} ⭐', callback_data=f'rate_{rated_user_id}_{i}')
    return builder.adjust(5).as_markup()




def intercity_hub_kb(lang, is_driver_mode: bool = False):
    builder = InlineKeyboardBuilder()
    m = MESSAGES.get(lang, MESSAGES['ru'])
    create_text = m.get('intercity_create_for_driver') if is_driver_mode else m.get('intercity_create_for_passenger')
    available_text = m.get('intercity_available_for_driver') if is_driver_mode else m.get('intercity_available_for_passenger')
    builder.button(text=create_text, callback_data='interhub_create_driver' if is_driver_mode else 'interhub_create_passenger')
    builder.button(text=available_text, callback_data='interhub_available_driver' if is_driver_mode else 'interhub_available_passenger')
    builder.button(text=_t(lang, 'btn_cancel_inline'), callback_data='interhub_cancel')
    return builder.adjust(1).as_markup()


def intercity_request_view_kb(lang):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_back_inline'), callback_data='interhub_cancel')
    return builder.as_markup()

def intercity_side_kb(lang, callback_prefix: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_from_my_city'), callback_data=f'{callback_prefix}_from')
    builder.button(text=_t(lang, 'btn_to_my_city'), callback_data=f'{callback_prefix}_to')
    builder.button(text=_t(lang, 'btn_cancel_inline'), callback_data=f'{callback_prefix}_cancel')
    return builder.adjust(1).as_markup()


def intercity_destinations_kb(lang: str, destinations: list[str], callback_prefix: str, mini_app_url: str | None = None, back_data: str | None = None, cancel_data: str | None = None):
    builder = InlineKeyboardBuilder()
    for idx, city in enumerate(destinations):
        builder.button(text=city, callback_data=f'{callback_prefix}_{idx}')
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_other_city', 'Other city'), web_app=mini_app_web_app(mini_app_url or '/'))
    if back_data:
        builder.button(text=_t(lang, 'btn_back_inline'), callback_data=back_data)
    if cancel_data:
        builder.button(text=_t(lang, 'btn_cancel_inline'), callback_data=cancel_data)
    return builder.adjust(2).as_markup()


def intercity_skip_kb(lang, callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_skip'), callback_data=callback_data)
    builder.button(text=_t(lang, 'btn_cancel_inline'), callback_data='intercity_common_cancel')
    return builder.adjust(1).as_markup()


def intercity_request_accept_kb(lang, request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru'])['btn_accept'], callback_data=f'intacc_{request_id}')
    return builder.as_markup()


def intercity_route_manage_kb(lang, route_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_change_price'), callback_data=f'routeprice_{route_id}')
    builder.button(text=_t(lang, 'btn_change_time'), callback_data=f'routetime_{route_id}')
    builder.button(text=_t(lang, 'btn_finish_route'), callback_data=f'routeoff_{route_id}')
    return builder.adjust(1).as_markup()


def current_intercity_request_kb(lang, request_id: int, show_pay: bool = False):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_change_price'), callback_data=f'icreqprice_{request_id}')
    builder.button(text=_t(lang, 'btn_change_time'), callback_data=f'icreqtime_{request_id}')
    if show_pay:
        builder.button(text=_t(lang, 'btn_pay_trip_balance'), callback_data=f'payintercity_{request_id}')
    builder.button(text=_t(lang, 'btn_cancel_inline'), callback_data=f'icreqcancel_{request_id}')
    return builder.adjust(1).as_markup()



def intercity_active_driver_kb(lang, request_id: int, status: str = 'active'):
    builder = InlineKeyboardBuilder()
    if status != 'arrived':
        builder.button(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_arrived', '📍 Arrived'), callback_data=f'icarrived_{request_id}')
    if status != 'in_progress':
        builder.button(text=_t(lang, 'btn_go_trip', '🚘 Go'), callback_data=f'icstart_{request_id}')
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_finish_order', '🏁 Finish trip'), callback_data=f'icfinish_{request_id}')
    builder.button(text=_t(lang, 'btn_complaint'), callback_data=f'compl_intercity_driver_{request_id}')
    builder.button(text=_t(lang, 'btn_cancel_inline', '❌ Cancel'), callback_data=f'icreqcancel_{request_id}')
    return builder.adjust(1).as_markup()


def intercity_active_passenger_kb(lang, request_id: int, show_pay: bool = False, allow_coming: bool = False):
    builder = InlineKeyboardBuilder()
    if show_pay:
        builder.button(text=_t(lang, 'btn_pay_trip_balance'), callback_data=f'payintercity_{request_id}')
    if allow_coming:
        builder.button(text=MESSAGES.get(lang, MESSAGES['ru']).get('btn_coming', '🚶 Coming'), callback_data=f'iccoming_{request_id}')
    builder.button(text=_t(lang, 'btn_complaint'), callback_data=f'compl_intercity_passenger_{request_id}')
    builder.button(text=_t(lang, 'btn_cancel_inline', '❌ Cancel'), callback_data=f'icreqcancel_{request_id}')
    return builder.adjust(1).as_markup()


def order_searching_kb(lang, order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_change_price'), callback_data=f'passprice_{order_id}')
    builder.button(text=_t(lang, 'btn_change_time'), callback_data=f'passtime_{order_id}')
    builder.button(text=_t(lang, 'btn_change_stop'), callback_data=f'passstop_{order_id}')
    builder.button(text=_t(lang, 'btn_change_pickup_note'), callback_data=f'passpicknote_{order_id}')
    builder.button(text=_t(lang, 'btn_change_destination_note'), callback_data=f'passdestnote_{order_id}')
    builder.button(text=_t(lang, 'btn_cancel_search'), callback_data=f'cancelsearch_{order_id}')
    return builder.adjust(1).as_markup()


def driver_offer_price_kb(lang, order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_offer_price'), callback_data=f'drv_offer_price_{order_id}')
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru'])['btn_accept'], callback_data=f'acc_{order_id}')
    return builder.adjust(1).as_markup()


def passenger_offer_response_kb(lang, order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_accept_price'), callback_data=f'acceptoffer_{order_id}')
    builder.button(text=_t(lang, 'btn_reject_price'), callback_data=f'rejectoffer_{order_id}')
    return builder.adjust(1).as_markup()


def payment_cards_kb(lang: str):
    builder = InlineKeyboardBuilder()
    labels = {
        'ru': [('💳 Uzcard', 'paycard_uzcard'), ('💳 Visa', 'paycard_visa')],
        'uz': [('💳 Uzcard', 'paycard_uzcard'), ('💳 Visa', 'paycard_visa')],
        'en': [('💳 Uzcard', 'paycard_uzcard'), ('💳 Visa', 'paycard_visa')],
        'ar': [('💳 Uzcard', 'paycard_uzcard'), ('💳 Visa', 'paycard_visa')],
    }
    for title, cb in labels.get(lang, labels['ru']):
        builder.button(text=title, callback_data=cb)
    return builder.adjust(1).as_markup()


def payment_admin_decision_kb(request_id: int, approve_text: str, reject_text: str, edit_text: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=approve_text, callback_data=f'approvepay_{request_id}')
    builder.button(text=edit_text, callback_data=f'editpay_{request_id}')
    builder.button(text=reject_text, callback_data=f'rejectpay_{request_id}')
    return builder.adjust(1).as_markup()


def inline_back_cancel_kb(lang, back_data: str | None = None, cancel_data: str | None = None):
    builder = InlineKeyboardBuilder()
    if back_data:
        builder.button(text=_t(lang, 'btn_back_inline'), callback_data=back_data)
    if cancel_data:
        builder.button(text=_t(lang, 'btn_cancel_inline'), callback_data=cancel_data)
    return builder.adjust(2).as_markup()


def intercity_route_list_kb(lang: str, route_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(lang, 'btn_accept_price'), callback_data=f'icrsel_{route_id}')
    builder.button(text=_t(lang, 'btn_offer_price'), callback_data=f'icroffer_{route_id}')
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru']).get('offer_details_btn', 'ℹ️ Подробнее'), callback_data=f'icdetail_{route_id}')
    return builder.adjust(1).as_markup()


def intercity_direct_driver_kb(lang: str, request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=MESSAGES.get(lang, MESSAGES['ru'])['btn_accept'], callback_data=f'idreqacc_{request_id}')
    builder.button(text=_t(lang, 'btn_reject_price'), callback_data=f'idreqrej_{request_id}')
    return builder.adjust(1).as_markup()


def intercity_date_input_kb(lang: str):
    labels = {
        'ru': '📅 Сегодня',
        'uz': '📅 Bugun',
        'en': '📅 Today',
        'ar': '📅 اليوم',
        'kz': '📅 Бүгін',
    }
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=labels.get(lang, labels['ru']))]], resize_keyboard=True)
