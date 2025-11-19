"""Router handling wallet selection and TON transfers."""

from __future__ import annotations

from contextlib import suppress

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import get_context
from app.db import (
    ActiveOrder,
    ActiveOrderRepository,
    CompletedTransaction,
    CompletedTransactionRepository,
    UserProfileRepository,
)
from app.filters import LocalizedButton
from app.keyboards import (
    cancel_keyboard,
    main_menu_keyboard,
    wallet_choice_keyboard,
    wallet_confirmation_keyboard,
)
from .states import SellingStates
from .utils import cancel_current_operation, resolve_language_tooling

router = Router(name="wallet")


@router.message(SellingStates.waiting_for_wallet_choice)
async def wallet_choice(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    profile_repo = UserProfileRepository(ctx.db_manager)
    profile = await profile_repo.get_profile(message.from_user.id)
    has_primary = bool(profile and profile.primary_wallet_address)

    text = (message.text or "").strip()
    if text == t("buttons.use_my_wallet"):
        if not has_primary:
            await message.answer(
                t("messages.sell_wallet_missing"),
                reply_markup=wallet_choice_keyboard(t, has_primary=False),
            )
            return
        await state.update_data(
            wallet_address=profile.primary_wallet_address,
            wallet_source="primary",
        )
        await state.set_state(SellingStates.confirming_wallet)
        await _send_wallet_summary(message, state, t)
    elif text == t("buttons.use_new_wallet"):
        await state.set_state(SellingStates.waiting_for_wallet)
        await message.answer(
            t("messages.sell_enter_wallet"),
            reply_markup=cancel_keyboard(t),
        )
    elif text == t("buttons.back"):
        await cancel_current_operation(message, state)
    else:
        await message.answer(
            t("messages.sell_wallet_choice"),
            reply_markup=wallet_choice_keyboard(t, has_primary=has_primary),
        )


@router.message(SellingStates.waiting_for_wallet)
async def collect_wallet_address(message: Message, state: FSMContext) -> None:
    await _save_wallet_address(message, state)


@router.message(
    LocalizedButton("confirm_address"), StateFilter(SellingStates.confirming_wallet)
)
async def confirm_wallet(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    stars_count = data.get("stars_count")
    ton_amount = data.get("ton_amount")
    payment_charge_id = data.get("payment_charge_id")

    if not all([wallet_address, stars_count, ton_amount]):
        await message.answer(
            t("messages.balance_check_failed"),
            reply_markup=main_menu_keyboard(t),
        )
        await state.clear()
        return

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
        "🔄 **...**",
        reply_markup=cancel_keyboard(t),
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
            await message.bot.delete_message(
                chat_id=processing.chat.id, message_id=processing.message_id
            )

        explorer_base = (
            "https://tonscan.org/tx"
            if ctx.settings.run_in_mainnet
            else "https://testnet.tonscan.org/tx"
        )
        success_text = (
            f"✅ {stars_count}⭐ / {ton_amount:.6f} TON\n"
            f"📥 {wallet_address}\n{explorer_base}/{tx_hash}"
        )
        await message.answer(
            success_text, reply_markup=main_menu_keyboard(t), parse_mode="Markdown"
        )
        await ctx.metrics.increment("ton_transfer_success")
    else:
        with suppress(Exception):
            await message.bot.delete_message(
                chat_id=processing.chat.id, message_id=processing.message_id
            )
        error_text = f"❌ {tx_hash}"
        await message.answer(
            error_text, reply_markup=cancel_keyboard(t), parse_mode="Markdown"
        )
        await ctx.metrics.increment("ton_transfer_failed")


@router.message(SellingStates.confirming_wallet)
async def update_wallet_during_confirmation(message: Message, state: FSMContext) -> None:
    await _save_wallet_address(message, state)


async def _save_wallet_address(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    text = (message.text or "").strip()
    if text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    wallet_address = text
    if not wallet_address.startswith(("EQ", "UQ", "0Q")):
        await message.answer(
            t("messages.wallet_invalid"),
            reply_markup=cancel_keyboard(t),
        )
        return

    is_valid = await ctx.ton_gateway.validate_address(wallet_address)
    if not is_valid:
        await message.answer(
            t("messages.wallet_invalid"),
            reply_markup=cancel_keyboard(t),
        )
        await ctx.metrics.increment("invalid_wallet_address")
        return

    await state.update_data(wallet_address=wallet_address)
    await state.set_state(SellingStates.confirming_wallet)
    await _send_wallet_summary(message, state, t)


async def _send_wallet_summary(message: Message, state: FSMContext, t) -> None:
    data = await state.get_data()
    stars_count = data.get("stars_count", 0)
    ton_amount = data.get("ton_amount", 0.0)
    wallet_address = data.get("wallet_address")
    summary = (
        f"📋\n⭐ {stars_count}\n"
        f"💰 {ton_amount:.6f} TON\n"
        f"📥 {wallet_address}"
    )
    await message.answer(
        summary,
        reply_markup=wallet_confirmation_keyboard(t),
        parse_mode="Markdown",
    )
