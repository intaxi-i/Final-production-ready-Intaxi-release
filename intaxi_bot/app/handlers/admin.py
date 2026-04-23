from __future__ import annotations

from aiogram import F, Bot, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.database.requests as rq
import app.keyboards as kb

router = Router()

ADMIN_PANEL_LABELS = {
    'ru': '🛡 Админ-панель',
    'uz': '🛡 Admin paneli',
    'en': '🛡 Admin panel',
    'ar': '🛡 لوحة الإدارة',
}

ROLE_LABELS = ('superadmin', 'admin', 'moderator', 'finance')

SECTION_BY_TEXT = {
    '📊 Dashboard': 'dashboard',
    '👥 Пользователи': 'users',
    '🚕 Водители': 'drivers',
    '💳 Финансы': 'finance',
    '🧾 Заказы': 'orders',
    '🛎 Модерация': 'moderation',
    '📢 Рассылка': 'broadcast',
    '💳 Пополнения': 'payments',
    '🔎 Пользователь по ID': 'lookup',
    '💬 Отзывы': 'feedback',
    '⚠️ Жалобы': 'complaints',
    '🛡 Админы': 'admins',
}


class AdminFlows(StatesGroup):
    lookup_id = State()
    grant_admin_id = State()


async def _clean_admin_messages(bot: Bot, user_tg_id: int) -> None:
    rows = await rq.get_cleanup_messages(user_tg_id, 'admin')
    for row in rows:
        try:
            await bot.delete_message(chat_id=row.chat_id, message_id=row.message_id)
        except Exception:
            pass
    await rq.clear_cleanup_messages(user_tg_id, 'admin')


async def _send_admin_block(target: types.Message | types.CallbackQuery, text: str, *, reply_markup=None, parse_mode: str | None = 'HTML'):
    bot = target.bot
    user_id = target.from_user.id
    chat_id = target.message.chat.id if isinstance(target, types.CallbackQuery) else target.chat.id
    await _clean_admin_messages(bot, user_id)
    sent = await bot.send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )
    await rq.track_cleanup_message(user_id, chat_id, sent.message_id, 'admin')
    return sent


async def _admin_context(user_id: int):
    user = await rq.get_or_create_user(user_id, '')
    lang = user.language or 'ru'
    role = await rq.get_admin_role(user_id)
    return user, lang, role


async def _ensure_permission(target: types.Message | types.CallbackQuery, permission: str) -> bool:
    allowed = await rq.admin_has_permission(target.from_user.id, permission)
    if not allowed:
        try:
            await target.answer('Недостаточно прав', show_alert=True)
        except Exception:
            pass
    return allowed


@router.message(F.text == '/admin')
@router.message(lambda message: message.text in ADMIN_PANEL_LABELS.values())
async def open_admin_panel(message: types.Message):
    if not await rq.is_admin_user(message.from_user.id):
        return
    user, lang, _role = await _admin_context(message.from_user.id)
    await message.answer('🛡', reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=False, is_admin=True))
    stats = await rq.get_basic_stats()
    text = (
        '<b>Админ-панель</b>\n\n'
        f'Пользователи: {stats["users"]}\n'
        f'Подтверждённые водители: {stats["drivers"]}\n'
        f'Активные городские заказы: {stats["active_city"]}\n'
        f'Активные маршруты: {stats["active_routes"]}\n'
        f'Активные межгород-заявки: {stats["active_requests"]}\n'
        f'Заявки на пополнение: {stats["pending_payments"]}'
    )
    await _send_admin_block(message, text)


@router.message(F.text == '👤 Режим пользователя')
async def switch_to_user_mode(message: types.Message, state: FSMContext):
    if not await rq.is_admin_user(message.from_user.id):
        return
    await state.clear()
    user, lang, _role = await _admin_context(message.from_user.id)
    await _clean_admin_messages(message.bot, user.tg_id)
    await message.answer(
        '👤',
        reply_markup=kb.main_menu(
            lang,
            user_id=user.tg_id,
            as_user=True,
            is_driver_mode=bool(user.is_verified and (user.active_role or 'driver') != 'passenger'),
            is_admin=True,
        ),
    )


@router.message(lambda message: message.text in SECTION_BY_TEXT)
async def open_admin_section(message: types.Message, state: FSMContext):
    section = SECTION_BY_TEXT[message.text]
    if not await _ensure_permission(message, section):
        return
    await state.clear()

    if section == 'dashboard':
        stats = await rq.get_basic_stats()
        text = (
            '<b>Dashboard</b>\n\n'
            f'👥 Пользователи: {stats["users"]}\n'
            f'🚕 Водители: {stats["drivers"]}\n'
            f'💳 Пополнения pending: {stats["pending_payments"]}\n'
            f'🧾 Активные city orders: {stats["active_city"]}\n'
            f'🛣 Активные routes: {stats["active_routes"]}\n'
            f'🙋 Активные requests: {stats["active_requests"]}'
        )
        await _send_admin_block(message, text)
        return

    if section == 'users':
        users = await rq.list_recent_users(12)
        lines = ['<b>Последние пользователи</b>']
        for user in users:
            lines.append(
                f'• <code>{user.tg_id}</code> — {user.full_name or "—"} | {user.country or "—"} / {user.city or "—"}'
            )
        await _send_admin_block(message, '\n'.join(lines))
        return

    if section == 'drivers':
        users = [u for u in await rq.list_recent_users(30) if u.is_verified]
        lines = ['<b>Водители</b>']
        if not users:
            lines.append('Нет подтверждённых водителей.')
        for user in users:
            lines.append(f'• <code>{user.tg_id}</code> — {user.full_name or "—"} | режим: {user.active_role or "driver"}')
        await _send_admin_block(message, '\n'.join(lines))
        return

    if section in {'finance', 'payments'}:
        rows = await rq.list_pending_driver_payments(10)
        lines = ['<b>Заявки на пополнение</b>']
        if not rows:
            lines.append('Pending заявок нет.')
        for row in rows:
            lines.append(f'• #{row.id} — TG <code>{row.driver_tg_id}</code> — {row.amount} — {row.status}')
        await _send_admin_block(message, '\n'.join(lines))
        return

    if section == 'orders':
        snapshot = await rq.list_orders_snapshot(8)
        role = await rq.get_admin_role(message.from_user.id)
        builder = InlineKeyboardBuilder()
        lines = ['<b>Активные заказы</b>']
        added_buttons = False
        for row in snapshot['city']:
            lines.append(f'🚕 city #{row.id} | TG <code>{row.creator_tg_id}</code> | {row.city} | {row.from_address} → {row.to_address or "—"}')
            if role == 'superadmin':
                builder.button(text=f'❌ city #{row.id}', callback_data=f'admincancel_city_{row.id}')
                added_buttons = True
        for row in snapshot['routes']:
            lines.append(f'🛣 route #{row.id} | TG <code>{row.creator_tg_id}</code> | {row.from_city} → {row.to_city}')
            if role == 'superadmin':
                builder.button(text=f'❌ route #{row.id}', callback_data=f'admincancel_route_{row.id}')
                added_buttons = True
        for row in snapshot['requests']:
            lines.append(f'🙋 request #{row.id} | TG <code>{row.creator_tg_id}</code> | {row.from_city} → {row.to_city}')
            if role == 'superadmin':
                builder.button(text=f'❌ request #{row.id}', callback_data=f'admincancel_request_{row.id}')
                added_buttons = True
        markup = builder.adjust(2).as_markup() if added_buttons else None
        await _send_admin_block(message, '\n'.join(lines), reply_markup=markup)
        return

    if section == 'moderation':
        feedback_rows = await rq.list_recent_feedback(8)
        lines = [
            '<b>Модерация</b>',
            'Проверь заявки водителей через сообщения с кнопками verify/reject.',
            '',
            '<b>Последние отзывы/предложения</b>',
        ]
        if not feedback_rows:
            lines.append('Новых записей нет.')
        for row in feedback_rows:
            lines.append(f'• #{row.id} | TG <code>{row.user_tg_id}</code> | {row.kind} | {row.content_type}')
        await _send_admin_block(message, '\n'.join(lines))
        return

    if section == 'broadcast':
        await _send_admin_block(message, '<b>Рассылка</b>\n\nМассовая рассылка в этом restore-bundle отключена, чтобы не сломать рабочие сценарии.')
        return

    if section == 'lookup':
        await state.set_state(AdminFlows.lookup_id)
        await _send_admin_block(message, 'Отправь Telegram ID пользователя одним сообщением.')
        return

    if section == 'feedback':
        rows = await rq.list_recent_feedback(12)
        lines = ['<b>Отзывы и предложения</b>']
        if not rows:
            lines.append('Пусто.')
        for row in rows:
            body = (row.text_value or '').strip()
            preview = body[:80] + ('…' if len(body) > 80 else '') if body else row.content_type
            lines.append(f'• #{row.id} | TG <code>{row.user_tg_id}</code> | {row.kind} | {preview}')
        await _send_admin_block(message, '\n'.join(lines))
        return

    if section == 'complaints':
        rows = await rq.list_recent_complaints(12)
        lines = ['<b>Жалобы</b>']
        if not rows:
            lines.append('Жалоб пока нет.')
        for row in rows:
            body = (row.text_value or '').strip()
            preview = body[:80] + ('…' if len(body) > 80 else '') if body else row.content_type
            lines.append(f'• #{row.id} | TG <code>{row.user_tg_id}</code> | {preview}')
        await _send_admin_block(message, '\n'.join(lines))
        return

    if section == 'admins':
        rows = await rq.list_admin_roles()
        builder = InlineKeyboardBuilder()
        lines = ['<b>Администраторы</b>']
        for row in rows:
            lines.append(f'• <code>{row.tg_id}</code> — {row.role}')
            builder.button(text=f'🔁 {row.tg_id}', callback_data=f'adminrole_pick_{row.tg_id}')
            builder.button(text=f'🗑 {row.tg_id}', callback_data=f'adminrevoke_{row.tg_id}')
        builder.button(text='➕ Назначить / сменить роль', callback_data='adminrole_add')
        await _send_admin_block(message, '\n'.join(lines), reply_markup=builder.adjust(2).as_markup())
        return


@router.message(AdminFlows.lookup_id)
async def lookup_user(message: types.Message, state: FSMContext):
    if not await _ensure_permission(message, 'lookup'):
        await state.clear()
        return
    text = (message.text or '').strip()
    if not text.isdigit():
        await message.answer('Нужен числовой Telegram ID.')
        return
    user = await rq.find_user_by_tg_id(int(text))
    await state.clear()
    if not user:
        await _send_admin_block(message, 'Пользователь не найден.')
        return
    text = (
        '<b>Пользователь</b>\n\n'
        f'ID: <code>{user.tg_id}</code>\n'
        f'Имя: {user.full_name or "—"}\n'
        f'Username: @{user.username or "—"}\n'
        f'Страна/город: {user.country or "—"} / {user.city or "—"}\n'
        f'Роль: {user.active_role or "passenger"}\n'
        f'Водитель подтверждён: {"да" if user.is_verified else "нет"}\n'
        f'Баланс: {user.balance or 0}'
    )
    await _send_admin_block(message, text)


@router.callback_query(F.data == 'adminrole_add')
async def adminrole_add(callback: types.CallbackQuery, state: FSMContext):
    if not await _ensure_permission(callback, 'admins'):
        return
    await state.set_state(AdminFlows.grant_admin_id)
    await _send_admin_block(callback, 'Отправь Telegram ID пользователя, которому нужно выдать или сменить роль.')
    await callback.answer()


@router.message(AdminFlows.grant_admin_id)
async def adminrole_add_receive_id(message: types.Message, state: FSMContext):
    if not await _ensure_permission(message, 'admins'):
        await state.clear()
        return
    value = (message.text or '').strip()
    if not value.isdigit():
        await message.answer('Нужен числовой Telegram ID.')
        return
    target_id = int(value)
    builder = InlineKeyboardBuilder()
    for role in ROLE_LABELS:
        builder.button(text=role, callback_data=f'adminrole_set_{target_id}_{role}')
    await state.clear()
    await _send_admin_block(message, f'Выбери роль для <code>{target_id}</code>.', reply_markup=builder.adjust(2).as_markup())


@router.callback_query(F.data.startswith('adminrole_pick_'))
async def adminrole_pick_existing(callback: types.CallbackQuery):
    if not await _ensure_permission(callback, 'admins'):
        return
    target_id = int(callback.data.rsplit('_', 1)[1])
    builder = InlineKeyboardBuilder()
    for role in ROLE_LABELS:
        builder.button(text=role, callback_data=f'adminrole_set_{target_id}_{role}')
    await _send_admin_block(callback, f'Смена роли для <code>{target_id}</code>.', reply_markup=builder.adjust(2).as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith('adminrole_set_'))
async def adminrole_set(callback: types.CallbackQuery):
    if not await _ensure_permission(callback, 'admins'):
        return
    _, _, target_id, role = callback.data.split('_', 3)
    await rq.revoke_admin_roles(int(target_id))
    await rq.set_admin_role(int(target_id), role, assigned_by=callback.from_user.id)
    await callback.answer('OK')
    await _send_admin_block(callback, f'Роль <b>{role}</b> выдана пользователю <code>{target_id}</code>.')


@router.callback_query(F.data.startswith('adminrevoke_'))
async def adminrole_revoke(callback: types.CallbackQuery):
    if not await _ensure_permission(callback, 'admins'):
        return
    target_id = int(callback.data.rsplit('_', 1)[1])
    if target_id == callback.from_user.id:
        await callback.answer('Нельзя снять свою роль из панели', show_alert=True)
        return
    target_role = await rq.get_admin_role(target_id)
    if target_role == 'superadmin' and await rq.count_active_admins_by_role('superadmin') <= 1:
        await callback.answer('Нельзя снять последнего superadmin', show_alert=True)
        return
    await rq.revoke_admin_roles(target_id)
    await _send_admin_block(callback, f'Все роли пользователя <code>{target_id}</code> сняты.')
    await callback.answer('OK')


@router.callback_query(F.data.startswith('admincancel_'))
async def admin_cancel_active_order(callback: types.CallbackQuery):
    if not await _ensure_permission(callback, 'orders'):
        return
    role = await rq.get_admin_role(callback.from_user.id)
    if role != 'superadmin':
        await callback.answer('Только superadmin', show_alert=True)
        return
    _, kind, raw_id = callback.data.split('_', 2)
    item_id = int(raw_id)
    if kind == 'city':
        row = await rq.cancel_city_order(item_id)
    elif kind == 'route':
        row = await rq.cancel_intercity_route(item_id)
    else:
        row = await rq.cancel_intercity_request(item_id)
    if not row:
        await callback.answer('Не найдено', show_alert=True)
        return
    await _send_admin_block(callback, f'Статус {kind} #{item_id} изменён на <b>{row.status}</b>.')
    await callback.answer('OK')
