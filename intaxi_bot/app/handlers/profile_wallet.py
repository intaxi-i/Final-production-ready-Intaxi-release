from __future__ import annotations

import html

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

import app.database.requests as rq
import app.keyboards as kb
from app.database.models import User, async_session
from app.handlers.profile import ADMIN_RECEIVING_CARDS, ayah_header, is_driver_mode, tr
from app.strings import MESSAGES

router = Router()


class DepositMoney(StatesGroup):
    amount = State()


class PaymentReceiptFlow(StatesGroup):
    receipt = State()


class AdminPaymentAdjustFlow(StatesGroup):
    amount = State()


async def _admin_lang(admin_id: int, default: str = 'ru') -> str:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == admin_id))
        return (user.language if user and user.language else default) or default


def _safe(value) -> str:
    return html.escape(str(value or '—'))


async def _notify_finance_admins(bot: Bot, *, payment_request_id: int, user, amount: float, card_country: str | None, card_number: str | None, receipt_file_id: str) -> None:
    admin_ids = await rq.get_admin_targets_by_permission('finance')
    card_data = ADMIN_RECEIVING_CARDS.get(card_country or '', {})
    for admin_id in admin_ids:
        lang = await _admin_lang(admin_id)
        caption = (
            f"{tr(lang, 'admin_receipt_new')}\n"
            f"{tr(lang, 'user_label')}: {_safe(user.full_name)}\n"
            f"TG ID: <code>{user.tg_id}</code>\n"
            f"{tr(lang, 'amount_label')}: <code>{_safe(amount)}</code>\n"
            f"{tr(lang, 'card_label')}: {_safe(str(card_country or '').upper())} | <code>{_safe(card_number)}</code>\n"
            f"{tr(lang, 'card_holder_label')}: {_safe(card_data.get('holder', '-'))}"
        )
        try:
            await bot.send_photo(
                admin_id,
                photo=receipt_file_id,
                caption=caption,
                reply_markup=kb.payment_admin_decision_kb(
                    payment_request_id,
                    tr(lang, 'correct_amount_btn'),
                    tr(lang, 'reject_payment_btn'),
                    tr(lang, 'edit_payment_amount_btn'),
                ),
                parse_mode='HTML',
            )
        except Exception:
            pass


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
        text += f"\n💳 <b>{tr(lang, 'driver_card_title')}:</b> {_safe(user.driver_card_country)} | <code>{_safe(user.driver_card_number)}</code>\n📋 {tr(lang, 'copy_hint')}\n"
    text += f"\n{tr(lang, 'wallet_help')}"
    await message.answer(ayah_header(lang) + text, reply_markup=builder.as_markup(), parse_mode='HTML')


@router.callback_query(F.data == 'deposit_start')
async def deposit_start(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    currency = MESSAGES[lang].get('currencies', {}).get(user.country, 'USD')
    await state.clear()
    await callback.message.answer(f"{tr(lang, 'enter_amount')} ({currency}):")
    await state.set_state(DepositMoney.amount)
    await callback.answer()


@router.message(DepositMoney.amount)
async def deposit_amount(message: types.Message, state: FSMContext):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    try:
        amount = float((message.text or '').replace(',', '.'))
    except Exception:
        await message.answer(tr(lang, 'enter_number'))
        return
    if amount <= 0:
        await message.answer(tr(lang, 'enter_number'))
        return
    await state.update_data(topup_amount=amount)
    await message.answer(tr(lang, 'choose_payment_card_country'), reply_markup=kb.payment_cards_kb(lang))


@router.callback_query(F.data.startswith('paycard_'))
async def choose_pay_card(callback: types.CallbackQuery, state: FSMContext):
    user = await rq.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    amount = float(data.get('topup_amount', 0) or 0)
    if amount <= 0:
        await state.clear()
        await callback.message.answer(f"{tr(lang, 'enter_amount')}:")
        await state.set_state(DepositMoney.amount)
        await callback.answer()
        return
    card_country = callback.data.split('_', 1)[1]
    card_data = ADMIN_RECEIVING_CARDS.get(card_country)
    if not card_data:
        await callback.answer(show_alert=True)
        return
    await state.update_data(admin_card_country=card_country, admin_card_number=card_data['number'])
    await state.set_state(PaymentReceiptFlow.receipt)
    await callback.message.answer(
        f"{_safe(card_data['label'])}\n<code>{_safe(card_data['number'])}</code>\n{tr(lang, 'card_holder_label')}: <b>{_safe(card_data['holder'])}</b>\n\n{tr(lang, 'send_receipt')}",
        parse_mode='HTML',
    )
    await callback.answer()


@router.message(PaymentReceiptFlow.receipt, F.photo)
async def receive_payment_receipt(message: types.Message, state: FSMContext, bot: Bot):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    lang = user.language or 'ru'
    data = await state.get_data()
    amount = float(data.get('topup_amount', 0) or 0)
    if amount <= 0:
        await state.clear()
        await message.answer(f"{tr(lang, 'enter_amount')}:")
        await state.set_state(DepositMoney.amount)
        return
    payment_request = await rq.create_driver_payment_request(
        driver_tg_id=message.from_user.id,
        card_country=data.get('admin_card_country'),
        admin_card_number=data.get('admin_card_number'),
        amount=amount,
        receipt_file_id=message.photo[-1].file_id,
    )
    await state.clear()
    await _notify_finance_admins(
        bot,
        payment_request_id=payment_request.id,
        user=user,
        amount=amount,
        card_country=data.get('admin_card_country'),
        card_number=data.get('admin_card_number'),
        receipt_file_id=message.photo[-1].file_id,
    )
    await message.answer(tr(lang, 'payment_request_sent'), reply_markup=kb.main_menu(lang, user_id=user.tg_id, as_user=True, is_driver_mode=is_driver_mode(user)))


@router.message(PaymentReceiptFlow.receipt)
async def receive_payment_receipt_wrong_type(message: types.Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(tr(user.language or 'ru', 'receipt_missing_photo'))


@router.callback_query(F.data.startswith('editpay_'))
async def edit_payment_amount_start(callback: types.CallbackQuery, state: FSMContext):
    if not await rq.admin_has_permission(callback.from_user.id, 'finance'):
        await callback.answer()
        return
    admin_lang = await _admin_lang(callback.from_user.id)
    request_id = int(callback.data.split('_', 1)[1])
    await state.clear()
    await state.update_data(payment_request_id=request_id, admin_lang=admin_lang)
    await state.set_state(AdminPaymentAdjustFlow.amount)
    await callback.message.answer(tr(admin_lang, 'enter_admin_topup_amount'))
    await callback.answer()


@router.message(AdminPaymentAdjustFlow.amount)
async def edit_payment_amount_finish(message: types.Message, state: FSMContext, bot: Bot):
    if not await rq.admin_has_permission(message.from_user.id, 'finance'):
        await state.clear()
        return
    data = await state.get_data()
    admin_lang = data.get('admin_lang') or await _admin_lang(message.from_user.id)
    request_id = data.get('payment_request_id')
    try:
        amount = float(str(message.text or '').replace(',', '.'))
    except Exception:
        await message.answer(tr(admin_lang, 'enter_number'))
        return
    updated = await rq.update_driver_payment_request_amount(request_id, amount)
    await state.clear()
    if not updated:
        await message.answer(tr(admin_lang, 'payment_rejected_admin'))
        return
    result = await rq.approve_driver_payment_request(request_id)
    if not result:
        await message.answer(tr(admin_lang, 'payment_rejected_admin'))
        return
    _, target_user = result
    lang = target_user.language or 'ru'
    await bot.send_message(target_user.tg_id, tr(lang, 'payment_approved_driver'), reply_markup=kb.main_menu(lang, user_id=target_user.tg_id, as_user=True, is_driver_mode=bool(target_user.is_verified and (target_user.active_role or 'driver') != 'passenger')))
    await message.answer(tr(admin_lang, 'payment_approved_admin') + f' ({amount})')


@router.callback_query(F.data.startswith('approvepay_'))
async def approve_payment(callback: types.CallbackQuery, bot: Bot):
    if not await rq.admin_has_permission(callback.from_user.id, 'finance'):
        await callback.answer()
        return
    admin_lang = await _admin_lang(callback.from_user.id)
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
    await callback.message.answer(tr(admin_lang, 'payment_approved_admin'))
    await callback.answer('OK')


@router.callback_query(F.data.startswith('rejectpay_'))
async def reject_payment(callback: types.CallbackQuery, bot: Bot):
    if not await rq.admin_has_permission(callback.from_user.id, 'finance'):
        await callback.answer()
        return
    admin_lang = await _admin_lang(callback.from_user.id)
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
    await callback.message.answer(tr(admin_lang, 'payment_rejected_admin'))
    await callback.answer('OK')
