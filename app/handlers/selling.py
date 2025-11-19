"""Router handling selling initiation and star count collection."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, Message

from app.context import get_context
from app.keyboards.common import Buttons, cancel_keyboard
from .states import SellingStates
from .utils import cancel_current_operation, resume_flow_if_needed

router = Router(name="selling")


@router.message(F.text == Buttons.START_SELLING)
async def start_selling(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    current_state = await state.get_state()
    if current_state and current_state != SellingStates.waiting_for_stars.state:
        await message.answer(
            "⚠️ لديك عملية قائمة بالفعل.",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        await resume_flow_if_needed(message, state)
        return

    success, balance = await ctx.ton_gateway.get_balance()
    if not success:
        await message.answer(
            "❌ **عذراً**\n\nلا يمكن بدء عملية جديدة بسبب مشكلة في التحقق من الرصيد.",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    if balance < 1.0:
        await message.answer(
            f"⚠️ **تنبيه**\n\nرصيد البوت الحالي: {balance:.6f} TON\nقد لا يكون كافياً لعمليات البيع الكبيرة.",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )

    await state.set_state(SellingStates.waiting_for_stars)
    await state.set_data({})
    await message.answer(
        "📤 **حسناً!**\n\nأرسل الآن **عدد النجوم** التي تريد بيعها:\n- يجب أن يكون العدد رقماً صحيحاً\n- مثال: 100",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )


@router.message(SellingStates.waiting_for_stars)
async def process_stars_count(message: Message, state: FSMContext) -> None:
    if message.text == Buttons.CANCEL_OPERATION:
        await cancel_current_operation(message, state)
        return

    ctx = get_context()
    try:
        stars_count = int(message.text)
    except ValueError:
        await message.answer(
            "❌ **إدخال غير صحيح**\n\nيرجى إدخال رقم صحيح فقط، مثال: 100",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    if stars_count <= 0:
        await message.answer(
            "❌ **العدد يجب أن يكون أكبر من الصفر**",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    if stars_count > 10000:
        await message.answer(
            "❌ **العدد كبير جداً**\nيرجى إدخال عدد أقل من 10000 نجمة",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    prices = await ctx.pricing_service.get_prices()
    ton_amount = stars_count * prices["star_ton"]

    success, balance = await ctx.ton_gateway.get_balance()
    if not success or balance < ton_amount:
        await message.answer(
            "❌ **رصيد غير كافٍ لإتمام العملية حالياً**",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown",
        )
        return

    await state.update_data(
        stars_count=stars_count,
        ton_amount=ton_amount,
    )

    payload = f"stars_payment:{message.from_user.id}:{stars_count}"
    prices_list = [LabeledPrice(label=f"{stars_count} نجمة", amount=stars_count)]

    await message.answer_invoice(
        title=f"بيع {stars_count} نجمة",
        description=f"بيع {stars_count} نجمة مقابل {ton_amount:.6f} TON",
        currency="XTR",
        prices=prices_list,
        provider_token=ctx.settings.payment_provider_token or "",
        payload=payload,
        start_parameter="stars-sale",
    )

    await state.set_state(SellingStates.waiting_for_payment)
    await message.answer(
        "💎 **تم إنشاء فاتورة الدفع**\n\nاضغط على الزر أعلاه لدفع النجوم.",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )
