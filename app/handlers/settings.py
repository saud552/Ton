"""Handlers for user settings such as language and wallet."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.context import get_context
from app.db import UserProfileRepository
from app.filters import LocalizedButton
from app.keyboards import cancel_keyboard, main_menu_keyboard
from .utils import cancel_current_operation, resolve_language_tooling


class SettingsStates(StatesGroup):
    waiting_for_wallet = State(state="settings_waiting_for_wallet")


router = Router(name="settings")


@router.message(LocalizedButton("change_language"))
async def prompt_language(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    langs = ctx.localization.available_languages()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
            for code, name in langs.items()
        ]
    )
    await message.answer(t("messages.language_prompt"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery) -> None:
    ctx = get_context()
    code = callback.data.split(":", maxsplit=1)[1]
    repo = UserProfileRepository(ctx.db_manager)
    await repo.upsert_partial(callback.from_user.id, language=code)

    def t_local(key: str, **kwargs):
        return ctx.localization.gettext(code, key, **kwargs)

    language_name = ctx.localization.gettext(code, f"languages.{code}")
    await callback.answer(
        t_local("messages.language_updated", language=language_name)
    )
    await callback.message.edit_text(
        t_local("messages.language_updated", language=language_name)
    )


@router.message(LocalizedButton("change_wallet"))
async def prompt_wallet_update(message: Message, state: FSMContext) -> None:
    _, t = await resolve_language_tooling(message.from_user.id)
    await state.set_state(SettingsStates.waiting_for_wallet)
    await message.answer(
        t("messages.sell_enter_wallet"),
        reply_markup=cancel_keyboard(t),
    )

@router.message(LocalizedButton("create_invoice"))
async def notify_invoice_creation(message: Message) -> None:
    _, t = await resolve_language_tooling(message.from_user.id)
    await message.answer(t("messages.feature_in_progress"))


@router.message(LocalizedButton("pay_invoice"))
async def notify_invoice_payment(message: Message) -> None:
    _, t = await resolve_language_tooling(message.from_user.id)
    await message.answer(t("messages.feature_in_progress"))


@router.message(StateFilter(SettingsStates.waiting_for_wallet))
async def update_primary_wallet(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    _, t = await resolve_language_tooling(message.from_user.id)
    text = (message.text or "").strip()
    if text == t("buttons.cancel"):
        await cancel_current_operation(message, state)
        return

    if not text.startswith(("EQ", "UQ", "0Q")):
        await message.answer(t("messages.wallet_invalid"), reply_markup=cancel_keyboard(t))
        return

    if not await ctx.ton_gateway.validate_address(text):
        await message.answer(t("messages.wallet_invalid"), reply_markup=cancel_keyboard(t))
        return

    repo = UserProfileRepository(ctx.db_manager)
    await repo.upsert_partial(message.from_user.id, primary_wallet_address=text)
    await state.clear()
    await message.answer(
        t("messages.wallet_saved"),
        reply_markup=main_menu_keyboard(t),
    )
