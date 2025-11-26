"""Router handling Telegram Stars payment events."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PreCheckoutQuery

from app.context import get_context
from app.db import UserProfileRepository
from app.keyboards import cancel_keyboard, wallet_choice_keyboard
from .states import SellingStates
from .utils import resolve_language_tooling

router = Router(name="payments")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload or ""
    parts = payload.split(":")
    stars_from_payload = int(parts[-1]) if len(parts) >= 3 and parts[-1].isdigit() else None

    data = await state.get_data()
    stars_count = data.get("stars_count") or stars_from_payload
    ton_amount = data.get("ton_amount")

    if stars_count is None or ton_amount is None:
        await message.answer(
            t("messages.balance_check_failed"),
            reply_markup=cancel_keyboard(t),
        )
        return

    profile_repo = UserProfileRepository(ctx.db_manager)
    profile = await profile_repo.get_profile(message.from_user.id)
    has_primary = bool(profile and profile.primary_wallet_address)

    await state.set_state(SellingStates.waiting_for_wallet_choice)
    await state.update_data(payment_charge_id=payment_info.telegram_payment_charge_id)

    success_text = t(
        "messages.payment_received",
        stars=stars_count,
        ton=f"{ton_amount:.6f}",
        charge=payment_info.telegram_payment_charge_id,
    )
    await message.answer(success_text, parse_mode="Markdown")

    prompt_key = (
        "messages.sell_wallet_choice"
        if has_primary
        else "messages.sell_wallet_missing"
    )
    await message.answer(
        t(prompt_key),
        reply_markup=wallet_choice_keyboard(t, has_primary=has_primary),
        parse_mode="Markdown",
    )
