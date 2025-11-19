"""Router handling selling initiation and star count collection."""

from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, Message

from app.context import get_context
from app.filters import LocalizedButton
from app.keyboards import cancel_keyboard
from .states import SellingStates
from .utils import cancel_current_operation, resolve_language_tooling, resume_flow_if_needed

router = Router(name="selling")


@router.message(LocalizedButton("sell_stars"))
async def start_selling(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    current_state = await state.get_state()
    if current_state and current_state != SellingStates.waiting_for_stars.state:
        await message.answer(
            t("messages.active_process_warning"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )
        await resume_flow_if_needed(message, state)
        return

    success, balance = await ctx.ton_gateway.get_balance()
    if not success:
        await message.answer(
            t("messages.balance_check_failed"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )
        return

    if balance < 1.0:
        await message.answer(
            t("messages.bot_balance_low", balance=f"{balance:.6f}"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )

    await state.set_state(SellingStates.waiting_for_stars)
    await state.set_data({})
    await message.answer(
        t("messages.sell_intro"),
        reply_markup=cancel_keyboard(t),
        parse_mode="Markdown",
    )


@router.message(SellingStates.waiting_for_stars)
async def process_stars_count(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    if message.text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    try:
        stars_count = int(message.text)
    except ValueError:
        await message.answer(
            t("messages.invalid_star_input"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )
        await ctx.metrics.increment("invalid_star_input")
        return

    if stars_count <= 0:
        await message.answer(
            t("messages.stars_out_of_range"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )
        await ctx.metrics.increment("stars_out_of_range")
        return

    if stars_count > 10000:
        await message.answer(
            t("messages.stars_out_of_range"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )
        await ctx.metrics.increment("stars_out_of_range")
        return

    prices = await ctx.pricing_service.get_prices()
    ton_amount = stars_count * prices["star_ton"]

    success, balance = await ctx.ton_gateway.get_balance()
    if not success or balance < ton_amount:
        await message.answer(
            t("messages.insufficient_liquidity"),
            reply_markup=cancel_keyboard(t),
            parse_mode="Markdown",
        )
        await ctx.metrics.increment("insufficient_liquidity")
        return

    await state.update_data(
        stars_count=stars_count,
        ton_amount=ton_amount,
    )

    payload = f"stars_payment:{message.from_user.id}:{stars_count}"
    prices_list = [LabeledPrice(label=f"{stars_count}⭐", amount=stars_count)]

    await message.answer_invoice(
        title=t("buttons.sell_stars"),
        description=f"{stars_count}⭐ = {ton_amount:.6f} TON",
        currency="XTR",
        prices=prices_list,
        provider_token=ctx.settings.payment_provider_token or "",
        payload=payload,
        start_parameter="stars-sale",
    )

    await state.set_state(SellingStates.waiting_for_payment)
    await message.answer(
        t("messages.invoice_created"),
        reply_markup=cancel_keyboard(t),
        parse_mode="Markdown",
    )
    await ctx.metrics.increment("invoices_created")
