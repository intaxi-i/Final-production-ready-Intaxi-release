from __future__ import annotations

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

import app.database.requests as rq
from app.database.models import User, async_session

router = Router()


class BroadcastFlow(StatesGroup):
    waiting_text = State()
    waiting_confirm = State()


async def _is_broadcast_admin(user_id: int) -> bool:
    return await rq.admin_has_permission(user_id, 'broadcast')


@router.message(F.text == '📢 Рассылка')
async def start_broadcast(message: types.Message, state: FSMContext):
    if not await _is_broadcast_admin(message.from_user.id):
        return
    await state.set_state(BroadcastFlow.waiting_text)
    await message.answer(
        '<b>Массовая рассылка включена.</b>\n\n'
        'Отправь текст сообщения для рассылки всем пользователям.\n'
        'Для отмены отправь: /cancel',
        parse_mode='HTML',
    )


@router.message(BroadcastFlow.waiting_text, F.text == '/cancel')
@router.message(BroadcastFlow.waiting_confirm, F.text == '/cancel')
async def cancel_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Рассылка отменена.')


@router.message(BroadcastFlow.waiting_text)
async def receive_broadcast_text(message: types.Message, state: FSMContext):
    if not await _is_broadcast_admin(message.from_user.id):
        await state.clear()
        return
    text = (message.html_text or message.text or '').strip()
    if not text:
        await message.answer('Текст пустой. Отправь текст рассылки или /cancel.')
        return
    async with async_session() as session:
        total = await session.scalar(select(User.tg_id).limit(1))
    await state.update_data(text=text)
    await state.set_state(BroadcastFlow.waiting_confirm)
    await message.answer(
        '<b>Подтверди рассылку</b>\n\n'
        f'{text}\n\n'
        'Отправь <code>ДА</code>, чтобы начать, или /cancel.',
        parse_mode='HTML',
        disable_web_page_preview=True,
    )


@router.message(BroadcastFlow.waiting_confirm)
async def confirm_broadcast(message: types.Message, state: FSMContext):
    if not await _is_broadcast_admin(message.from_user.id):
        await state.clear()
        return
    if (message.text or '').strip().upper() != 'ДА':
        await message.answer('Нужно отправить ДА для запуска или /cancel для отмены.')
        return
    data = await state.get_data()
    text = str(data.get('text') or '').strip()
    await state.clear()
    if not text:
        await message.answer('Текст рассылки потерян. Начни заново.')
        return
    async with async_session() as session:
        user_ids = (await session.scalars(select(User.tg_id).where(User.tg_id != message.from_user.id))).all()
    sent = 0
    failed = 0
    for tg_id in user_ids:
        try:
            await message.bot.send_message(int(tg_id), text, parse_mode='HTML', disable_web_page_preview=True)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f'Рассылка завершена. Отправлено: {sent}. Ошибок: {failed}.')
