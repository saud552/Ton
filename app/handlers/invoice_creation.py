"""Invoice creation flow handlers."""

from __future__ import annotations

from contextlib import suppress

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.context import get_context
from app.db import UserProfileRepository, UserRepository
from app.filters import LocalizedButton
from app.keyboards import cancel_keyboard, wallet_choice_keyboard
from .states import InvoiceCreationStates
from .utils import cancel_current_operation, resolve_language_tooling

router = Router(name="invoice_creation")


@router.message(LocalizedButton("create_invoice"))
async def start_invoice_creation(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    await state.clear()
    await state.set_state(InvoiceCreationStates.waiting_for_wallet_choice)

    repo = UserProfileRepository(ctx.db_manager)
    profile = await repo.get_profile(message.from_user.id)
    has_primary = bool(profile and profile.primary_wallet_address)

    prompt = (
        t("messages.invoice_wallet_prompt")
        if has_primary
        else t("messages.sell_wallet_missing")
    )
    await message.answer(
        prompt,
        reply_markup=wallet_choice_keyboard(t, has_primary=has_primary),
    )


@router.message(StateFilter(InvoiceCreationStates.waiting_for_wallet_choice))
async def invoice_wallet_choice(message: Message, state: FSMContext) -> None:
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
        await state.update_data(wallet_address=profile.primary_wallet_address)
        await state.set_state(InvoiceCreationStates.waiting_for_payer)
        await _prompt_payer(message, state, t)
    elif text == t("buttons.use_new_wallet"):
        await state.set_state(InvoiceCreationStates.waiting_for_wallet)
        await message.answer(
            t("messages.sell_enter_wallet"),
            reply_markup=cancel_keyboard(t),
        )
    elif text == t("buttons.back"):
        await cancel_current_operation(message, state)
    else:
        await message.answer(
            t("messages.invoice_wallet_prompt"),
            reply_markup=wallet_choice_keyboard(t, has_primary=has_primary),
        )


@router.message(StateFilter(InvoiceCreationStates.waiting_for_wallet))
async def invoice_wallet_entry(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    text = (message.text or "").strip()
    if text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    if not text.startswith(("EQ", "UQ", "0Q")):
        await message.answer(t("messages.wallet_invalid"), reply_markup=cancel_keyboard(t))
        return

    is_valid = await ctx.ton_gateway.validate_address(text)
    if not is_valid:
        await message.answer(t("messages.wallet_invalid"), reply_markup=cancel_keyboard(t))
        return

    await state.update_data(wallet_address=text)
    await state.set_state(InvoiceCreationStates.waiting_for_payer)
    await _prompt_payer(message, state, t)


async def _prompt_payer(message: Message, state: FSMContext, t) -> None:
    await message.answer(
        t("messages.invoice_payer_prompt"),
        reply_markup=cancel_keyboard(t),
    )


@router.message(StateFilter(InvoiceCreationStates.waiting_for_payer))
async def process_payer(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    text = (message.text or "").strip()
    if text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    payer_id = None
    payer_label = text
    if text.isdigit():
        payer_id = int(text)
    elif text.startswith("@") and len(text) > 1:
        username = text[1:]
        repo = UserRepository(ctx.db_manager)
        user = await repo.get_by_username(username)
        if user:
            payer_id = user.user_id
            payer_label = f"@{username}"
        else:
            try:
                chat = await message.bot.get_chat(username)
                payer_id = chat.id
                payer_label = chat.full_name or f"@{username}"
            except Exception:
                payer_id = None
    else:
        payer_id = None

    if payer_id is None:
        await message.answer(
            t("messages.invoice_payer_invalid"),
            reply_markup=cancel_keyboard(t),
        )
        return

    await state.update_data(payer_user_id=payer_id, payer_label=payer_label)
    await state.set_state(InvoiceCreationStates.waiting_for_reason)
    await message.answer(t("messages.invoice_reason_prompt"), reply_markup=cancel_keyboard(t))


@router.message(StateFilter(InvoiceCreationStates.waiting_for_reason))
async def process_reason(message: Message, state: FSMContext) -> None:
    _, t = await resolve_language_tooling(message.from_user.id)
    text = message.text.strip() if message.text else ""
    if text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    await state.update_data(reason=text)
    await state.set_state(InvoiceCreationStates.waiting_for_stars)
    await message.answer(t("messages.invoice_stars_prompt"), reply_markup=cancel_keyboard(t))


@router.message(StateFilter(InvoiceCreationStates.waiting_for_stars))
async def process_invoice_stars(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    text = (message.text or "").strip()
    if text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    try:
        stars = int(text)
    except ValueError:
        await message.answer(t("messages.invalid_star_input"), reply_markup=cancel_keyboard(t))
        return

    if stars <= 0 or stars > 10000:
        await message.answer(t("messages.stars_out_of_range"), reply_markup=cancel_keyboard(t))
        return

    prices = await ctx.pricing_service.get_prices()
    usd_value = stars * prices["star_usd"]
    ton_value = stars * prices["star_ton"]
    await state.update_data(
        stars_count=stars,
        usd_value=usd_value,
        ton_value=ton_value,
    )

    data = await state.get_data()
    summary = t(
        "messages.invoice_summary",
        wallet=data.get("wallet_address"),
        payer=data.get("payer_label"),
        reason=data.get("reason"),
        stars=stars,
        usd=f"{usd_value:.2f}",
        ton=f"{ton_value:.6f}",
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("buttons.confirm_invoice"), callback_data="invoice:create")],
            [InlineKeyboardButton(text=t("buttons.cancel"), callback_data="invoice:cancel")],
        ]
    )
    await state.set_state(InvoiceCreationStates.awaiting_confirmation)
    await message.answer(summary, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(StateFilter(InvoiceCreationStates.awaiting_confirmation), F.data == "invoice:cancel")
async def cancel_invoice_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    _, t = await resolve_language_tooling(callback.from_user.id)
    await callback.answer(t("messages.operation_cancelled"))
    await callback.message.edit_text(t("messages.operation_cancelled"))


@router.callback_query(StateFilter(InvoiceCreationStates.awaiting_confirmation), F.data == "invoice:create")
async def confirm_invoice(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(callback.from_user.id)
    data = await state.get_data()
    pricing = await ctx.pricing_service.get_prices()

    invoice = await ctx.invoice_service.create_invoice(
        creator_id=callback.from_user.id,
        payer_user_id=data.get("payer_user_id"),
        wallet_address=data.get("wallet_address"),
        reason=data.get("reason", ""),
        stars_count=data.get("stars_count"),
        star_price_usd=pricing["star_usd"],
        star_price_ton=pricing["star_ton"],
    )

    await state.clear()
    await callback.answer(t("messages.invoice_created_detail", code=invoice.code))
    await callback.message.edit_text(
        t("messages.invoice_created_detail", code=invoice.code)
    )
*** End of File
