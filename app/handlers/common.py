"""Common handlers such as cancellation and fallbacks."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.common import Buttons, main_menu_keyboard
from .utils import cancel_current_operation

router = Router(name="common")


@router.message(Command("cancel"))
@router.message(F.text == Buttons.CANCEL_OPERATION)
async def cancel_operation(message: Message, state: FSMContext) -> None:
    await cancel_current_operation(message, state)


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "🔍 **تعذر فهم الرسالة**\n\nاستخدم الأزرار أو الأوامر للتفاعل مع البوت.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
