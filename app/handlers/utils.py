"""Utilities shared across routers."""

from __future__ import annotations

from typing import Dict

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import get_context
from app.db import ActiveOrderRepository
from app.keyboards.common import Buttons, cancel_keyboard, main_menu_keyboard, wallet_confirmation_keyboard
from .states import SellingStates


async def resume_flow_if_needed(message: Message, state: FSMContext) -> bool:
    current_state = await state.get_state()
    if not current_state:
        return False

    data = await state.get_data()
    stars = data.get("stars_count", 0)
    ton_amount = data.get("ton_amount", 0.0)
    wallet_address = data.get("wallet_address")

    if current_state == SellingStates.waiting_for_stars.state:
        text = (
            "⚠️ **متابعة العملية**\n\n"
            "لديك عملية بيع غير مكتملة.\n"
            "أرسل عدد النجوم الذي ترغب في بيعه لاستكمال العملية."
        )
        markup = cancel_keyboard()
    elif current_state == SellingStates.waiting_for_payment.state:
        text = (
            "💳 **في انتظار الدفع**\n\n"
            f"عدد النجوم: {stars}\n"
            f"المبلغ المستحق: {ton_amount:.6f} TON\n\n"
            "أكمل دفع الفاتورة التي استلمتها أو ألغ العملية لإعادة البدء."
        )
        markup = cancel_keyboard()
    elif current_state == SellingStates.waiting_for_wallet.state:
        text = (
            "💎 **تم استلام النجوم**\n\n"
            f"عدد النجوم: {stars}\n"
            f"المبلغ المستحق: {ton_amount:.6f} TON\n\n"
            "الرجاء إرسال عنوان محفظة TON الخاصة بك لإتمام التحويل."
        )
        markup = cancel_keyboard()
    else:
        text = (
            "✅ **في انتظار التأكيد**\n\n"
            f"عدد النجوم: {stars}\n"
            f"المبلغ المستحق: {ton_amount:.6f} TON\n"
            f"العنوان الحالي: {wallet_address or 'غير متوفر'}\n\n"
            "اضغط على 'تأكيد العنوان ✅' لمتابعة التحويل أو قم بإلغائها."
        )
        markup = wallet_confirmation_keyboard()

    await message.answer(text, reply_markup=markup, parse_mode="Markdown")
    return True


def format_welcome(full_name: str, prices: Dict[str, float]) -> str:
    star_price_usd = prices.get("star_usd")
    star_price_ton = prices.get("star_ton")
    return f"""
مرحباً {full_name or 'عزيزي'} 👋

⚡️ **وظيفة البوت**:  
أنا بوت متخصص لشراء **النجوم** منك مقابل عملات **TON**.

💰 **سعر الصرف**:  
سعر النجم الواحد = {star_price_usd:.4f}$  
أي أن كل نجم يعادل {star_price_ton:.6f} TON

🚀 **كيفية البيع**:  
1️⃣ اضغط على زر '{Buttons.START_SELLING}'  
2️⃣ أرسل عدد النجوم التي تريد بيعها  
3️⃣ سنقوم بإنشاء فاتورة دفع للنجوم  
4️⃣ بعد الدفع، أرسل عنوان محفظتك على Tonkeeper  
5️⃣ سنقوم بتحويل TON لك فور التأكد

اضغط على الزر أدناه لبدء عملية البيع!
"""


async def cancel_current_operation(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    await state.clear()
    active_repo = ActiveOrderRepository(ctx.db_manager)
    await active_repo.delete_by_user(message.from_user.id)
    await message.answer(
        "❌ **تم إلغاء العملية**\\nيمكنك البدء من جديد في أي وقت!",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


__all__ = ["resume_flow_if_needed", "format_welcome", "cancel_current_operation"]
