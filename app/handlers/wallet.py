"""Router handling wallet collection and TON transfers."""

from __future__ import annotations

from contextlib import suppress

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import get_context
from app.db import ActiveOrder, ActiveOrderRepository, CompletedTransaction, CompletedTransactionRepository
from app.keyboards.common import Buttons, cancel_keyboard, main_menu_keyboard, wallet_confirmation_keyboard
from .states import SellingStates
from .utils import cancel_current_operation

router = Router(name="wallet")


@router.message(SellingStates.waiting_for_wallet)
async def collect_wallet_address(message: Message, state: FSMContext) -> None:
    await _save_wallet_address(message, state)


@router.message(SellingStates.confirming_wallet, F.text == Buttons.CONFIRM_ADDRESS)
async def confirm_wallet(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    stars_count = data.get("stars_count")
    ton_amount = data.get("ton_amount")
    payment_charge_id = data.get("payment_charge_id")

    if not all([wallet_address, stars_count, ton_amount]):
        await message.answer(
            "⚠️ البيانات غير مكتملة. يرجى البدء من جديد.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        return

    ctx = get_context()
    active_repo = ActiveOrderRepository(ctx.db_manager)
    tx_repo = CompletedTransactionRepository(ctx.db_manager)

    await active_repo.create_order(
        ActiveOrder(
            id=None,
            user_id=message.from_user.id,
            stars_count=stars_count,
            ton_amount=ton_amount,
            wallet_address=wallet_address,
            payment_charge_id=payment_charge_id,
            status="pending",
            created=None,
        )
    )

    processing = await message.answer(
        "🔄 **جاري معالجة التحويل...**\nقد تستغرق العملية بضع دقائق.",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )

    success, tx_hash = await ctx.ton_gateway.send_ton(wallet_address, ton_amount)

    if success:
        await tx_repo.record_transaction(
            CompletedTransaction(
                id=None,
                user_id=message.from_user.id,
                tx_hash=tx_hash,
                stars_count=stars_count,
                ton_amount=ton_amount,
                wallet_address=wallet_address,
                payment_charge_id=payment_charge_id,
                status="completed",
                created=None,
                completed_at=None,
            )
        )
        await active_repo.delete_by_user(message.from_user.id)
        await state.clear()
        with suppress(Exception):
            await message.bot.delete_message(chat_id=processing.chat.id, message_id=processing.message_id)

        explorer_base = "https://tonscan.org/tx" if ctx.settings.run_in_mainnet else "https://testnet.tonscan.org/tx"
        success_text = f"""
✅ **تمت العملية بنجاح!**

⭐ **عدد النجوم المستلمة:** {stars_count}  
💰 **المبلغ المحول:** {ton_amount:.6f} TON  
📥 **عنوان المحفظة:** {wallet_address}  
🔗 **هاش المعاملة:** {tx_hash}

يمكنك المتابعة هنا: {explorer_base}/{tx_hash}
"""
        await message.answer(success_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    else:
        with suppress(Exception):
            await message.bot.delete_message(chat_id=processing.chat.id, message_id=processing.message_id)
        error_text = f"""
❌ **حدث خطأ في التحويل**

لم نتمكن من إرسال TON إلى محفظتك.  
**السبب:** {tx_hash}

تم تسجيل طلبك وسنقوم بالمعالجة اليدوية. يرجى التواصل مع الدعم وذكر رقم المستخدم: {message.from_user.id}
"""
        await message.answer(error_text, reply_markup=cancel_keyboard(), parse_mode="Markdown")


@router.message(SellingStates.confirming_wallet)
async def update_wallet_during_confirmation(message: Message, state: FSMContext) -> None:
    await _save_wallet_address(message, state)


async def _save_wallet_address(message: Message, state: FSMContext) -> None:
    if message.text == Buttons.CANCEL_OPERATION:
        await cancel_current_operation(message, state)
        return

    wallet_address = message.text.strip()
    if not wallet_address.startswith(("EQ", "UQ", "0Q")):
        await message.answer(
            "❌ **عنوان محفظة غير صحيح**\nيرجى إرسال عنوان يبدأ بـ EQ أو UQ.",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    ctx = get_context()
    is_valid = await ctx.ton_gateway.validate_address(wallet_address)
    if not is_valid:
        await message.answer(
            "❌ **العنوان غير صالح أو غير نشط على شبكة TON**",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    data = await state.get_data()
    stars_count = data.get("stars_count", 0)
    ton_amount = data.get("ton_amount", 0.0)

    await state.update_data(wallet_address=wallet_address)
    await state.set_state(SellingStates.confirming_wallet)

    summary = f"""
📋 **تفاصيل طلبك النهائية:**

⭐ **عدد النجوم:** {stars_count}  
💰 **المبلغ المستحق:** {ton_amount:.6f} TON  
📥 **عنوان المحفظة:** {wallet_address}

اضغط على '{Buttons.CONFIRM_ADDRESS}' للمواصلة، أو '{Buttons.CANCEL_OPERATION}' للإلغاء.
"""
    await message.answer(summary, reply_markup=wallet_confirmation_keyboard(), parse_mode="Markdown")
