from __future__ import annotations

import html

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.database.requests as rq
import app.keyboards as kb
from app.database.models import User, async_session
from app.handlers.profile import is_driver_mode, tr
from app.strings import MESSAGES
from sqlalchemy import select

router = Router()


class FeedbackFlow(StatesGroup):
    kind = State()
    content = State()


async def _admin_lang(admin_id: int, default: str = 'ru') -> str:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == admin_id))
        return (user.language if user and user.language else default) or default


async def _send_feedback_to_admins(bot: Bot, *, user, kind: str, entry_id: int | str, text_value: str | None = None, voice_file_id: str | None = None) -> None:
    admin_ids = await rq.get_admin_targets_by_permission('moderation')
    safe_name = html.escape(user.full_name or '—')
    safe_username = html.escape(user.username or '—')
    for admin_id in admin_ids:
        lang = await _admin_lang(admin_id)
        kind_label = tr(lang, 'feedback_kind_' + kind, kind)
        base = (
            f"💬 <b>{tr(lang, 'feedback_title')}</b>\n\n"
            f"{tr(lang, 'feedback_type')}: {kind_label}\n"
            f"{tr(lang, 'feedback_from')}: {safe_name}\n"
            f"@{safe_username} | ID: <code>{user.tg_id}</code>\n"
            f"#feedback_{entry_id}"
        )
        try:
            if voice_file_id:
                await bot.send_voice(admin_id, voice=voice_file_id, caption=base, parse_mode='HTML')
            else:
                safe_text = html.escape(text_value or '')
                await bot.send_message(admin_id, f"{base}\n\n{safe_text}", parse_mode='HTML', disable_web_page_preview=True)
        except Exception:
            pass


@router.message(lambda message: any(message.text == MESSAGES[l].get('btn_feedback', '💬 Отзывы и предложения') for l in MESSAGES))
async def feedback_start(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(lang, 'feedback_kind_feedback'), callback_data='feedback_kind_feedback_v2')
    builder.button(text=tr(lang, 'feedback_kind_suggestion'), callback_data='feedback_kind_suggestion_v2')
    builder.adjust(1)
    await state.clear()
    await message.answer(tr(lang, 'feedback_prompt'), reply_markup=builder.as_markup())
    await state.set_state(FeedbackFlow.kind)


@router.callback_query(F.data.startswith('feedback_kind_'), FeedbackFlow.kind)
async def feedback_kind_selected(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    kind = callback.data.replace('_v2', '').split('feedback_kind_', 1)[1]
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
    await _send_feedback_to_admins(bot, user=user, kind=kind, entry_id=entry.id if entry else 'new', voice_file_id=message.voice.file_id)
    await message.answer(tr(lang, 'feedback_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.message(FeedbackFlow.content)
async def feedback_text_received(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    kind = data.get('feedback_kind', 'feedback')
    text_value = message.text or ''
    entry = await rq.create_feedback_entry(user.tg_id, kind, 'text', text_value=text_value)
    await state.clear()
    await _send_feedback_to_admins(bot, user=user, kind=kind, entry_id=entry.id if entry else 'new', text_value=text_value)
    await message.answer(tr(lang, 'feedback_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))
