"""Router handling /start and welcome flow."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import get_context
from app.db import User, UserRepository
from app.keyboards.common import main_menu_keyboard, start_keyboard
from .utils import format_welcome, resume_flow_if_needed

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    user_repo = UserRepository(ctx.db_manager)
    await user_repo.upsert_user(
        User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
    )

    prices = await ctx.pricing_service.get_prices()
    welcome_text = format_welcome(message.from_user.full_name or message.from_user.first_name, prices)
    await message.answer(welcome_text, reply_markup=start_keyboard(), parse_mode="Markdown")

    resumed = await resume_flow_if_needed(message, state)
    if not resumed:
        await message.answer(
            "يمكنك البدء الآن باستخدام الأزرار أدناه.",
            reply_markup=main_menu_keyboard(),
        )
