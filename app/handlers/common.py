"""Common handlers such as cancellation and fallbacks."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.filters import LocalizedButton
from app.keyboards import main_menu_keyboard
from .utils import cancel_current_operation, resolve_language_tooling

router = Router(name="common")


@router.message(Command("cancel"))
@router.message(LocalizedButton("cancel"))
async def cancel_operation(message: Message, state: FSMContext) -> None:
    await cancel_current_operation(message, state)


@router.message()
async def fallback(message: Message) -> None:
    _, t = await resolve_language_tooling(message.from_user.id)
    await message.answer(
        t("messages.unknown_command"),
        reply_markup=main_menu_keyboard(t),
        parse_mode="Markdown",
    )
