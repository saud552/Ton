"""Router handling Telegram Stars payment events."""

from __future__ import annotations

from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PreCheckoutQuery

from app.context import get_context
from app.keyboards.common import cancel_keyboard
from .states import SellingStates

router = Router(name="payments")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext) -> None:
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload or ""
    parts = payload.split(":")
    stars_from_payload = int(parts[-1]) if len(parts) >= 3 and parts[-1].isdigit() else None

    data = await state.get_data()
    stars_count = data.get("stars_count") or stars_from_payload
    ton_amount = data.get("ton_amount")

    if stars_count is None or ton_amount is None:
        await message.answer(
            "⚠️ حدث خلل في استرجاع بيانات الطلب. يرجى التواصل مع الدعم.",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.set_state(SellingStates.waiting_for_wallet)
    await state.update_data(payment_charge_id=payment_info.telegram_payment_charge_id)

    success_text = f"""
🎉 **تم استلام الدفع بنجاح!**

⭐ **عدد النجوم المستلمة:** {stars_count}  
💎 **المبلغ المستحق:** {ton_amount:.6f} TON  
🆔 **معرّف الدفع:** {payment_info.telegram_payment_charge_id}

الآن أرسل عنوان محفظتك على TON (يبدأ بـ EQ أو UQ) لإتمام التحويل.
"""
    await message.answer(success_text, reply_markup=cancel_keyboard(), parse_mode="Markdown")
