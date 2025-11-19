"""Utilities shared across routers."""

from __future__ import annotations

from typing import Callable, Dict, Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import get_context
from app.db import ActiveOrderRepository, UserProfileRepository
from app.keyboards.common import (
    cancel_keyboard,
    main_menu_keyboard,
    wallet_confirmation_keyboard,
)
from .states import SellingStates

Translator = Callable[[str, bool], str]


async def resolve_language_tooling(user_id: int) -> Tuple[str, Callable[[str], str]]:
    ctx = get_context()
    repo = UserProfileRepository(ctx.db_manager)
    profile = await repo.get_profile(user_id)
    if not profile:
        await repo.ensure_profile(user_id, default_language=ctx.settings.default_user_language)
        language = ctx.settings.default_user_language
    else:
        language = profile.language or ctx.settings.default_user_language

    def t(key: str, **kwargs) -> str:
        return ctx.localization.gettext(language, key, **kwargs)

    return language, t


async def resume_flow_if_needed(message: Message, state: FSMContext) -> bool:
    current_state = await state.get_state()
    if not current_state:
        return False

    _, t = await resolve_language_tooling(message.from_user.id)
    data = await state.get_data()
    stars = data.get("stars_count", 0)
    ton_amount = data.get("ton_amount", 0.0)
    wallet_address = data.get("wallet_address")

    if current_state == SellingStates.waiting_for_stars.state:
        text = t("messages.sell_intro")
        markup = cancel_keyboard(t)
    elif current_state == SellingStates.waiting_for_payment.state:
        text = (
            "💳 **في انتظار الدفع**\n\n"
            f"{t('messages.sell_intro')}\n"
            f"{stars} ⭐ / {ton_amount:.6f} TON"
        )
        markup = cancel_keyboard(t)
    elif current_state == SellingStates.waiting_for_wallet.state:
        text = t("messages.sell_wallet_choice")
        markup = cancel_keyboard(t)
    else:
        text = (
            "✅ **في انتظار التأكيد**\n\n"
            f"{stars} ⭐ / {ton_amount:.6f} TON\n"
            f"{t('messages.sell_wallet_choice')} {wallet_address or '-'}"
        )
        markup = wallet_confirmation_keyboard(t)

    await message.answer(text, reply_markup=markup, parse_mode="Markdown")
    return True


def format_welcome(full_name: str, prices: Dict[str, float], t: Callable[[str], str]) -> str:
    star_price_usd = prices.get("star_usd")
    star_price_ton = prices.get("star_ton")
    return t(
        "messages.start_welcome",
        name=full_name or "user",
        star_price_usd=star_price_usd,
        star_price_ton=star_price_ton,
    )


async def cancel_current_operation(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    await state.clear()
    active_repo = ActiveOrderRepository(ctx.db_manager)
    await active_repo.delete_by_user(message.from_user.id)
    await message.answer(
        t("messages.operation_cancelled"),
        reply_markup=main_menu_keyboard(t),
        parse_mode="Markdown",
    )


__all__ = [
    "resolve_language_tooling",
    "resume_flow_if_needed",
    "format_welcome",
    "cancel_current_operation",
]
