"""Router handling /start and welcome flow."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import get_context
from app.db import User, UserRepository
from app.filters import LocalizedButton
from app.keyboards import main_menu_keyboard, start_keyboard, subscription_keyboard
from app.services.subscription import check_subscription
from .utils import format_welcome, resolve_language_tooling, resume_flow_if_needed

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    user_id = message.from_user.id
    language, t = await resolve_language_tooling(user_id)

    if ctx.maintenance.enabled:
        await message.answer(
            t("messages.maintenance", message=ctx.maintenance.message)
        )
        return

    user_repo = UserRepository(ctx.db_manager)
    await user_repo.upsert_user(
        User(
            user_id=user_id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
    )

    allowed, missing = await check_subscription(
        message.bot, user_id, ctx.forced_subscription
    )
    if not allowed:
        await _prompt_subscription(message, missing, t)
        return

    await _send_home(message, state, t, ctx)


@router.message(LocalizedButton("check_subscription"))
async def handle_subscription_check(message: Message, state: FSMContext) -> None:
    ctx = get_context()
    user_id = message.from_user.id
    language, t = await resolve_language_tooling(user_id)
    allowed, missing = await check_subscription(
        message.bot, user_id, ctx.forced_subscription
    )
    if not allowed:
        await _prompt_subscription(message, missing, t)
        return

    await message.answer(t("messages.subscription_ok"))
    await _send_home(message, state, t, ctx)


async def _prompt_subscription(message: Message, missing_channels, t):
    if not missing_channels:
        missing_channels = []
    lines = "\n".join(f"• {channel}" for channel in missing_channels)
    prompt = (
        f"{t('messages.forced_subscription')}\n{lines}\n\n"
        f"{t('messages.subscription_confirm')}"
    )
    await message.answer(
        prompt,
        reply_markup=subscription_keyboard(t),
        disable_web_page_preview=True,
    )


async def _send_home(
    message: Message, state: FSMContext, t, ctx
) -> None:
    prices = await ctx.pricing_service.get_prices()
    welcome_text = format_welcome(
        message.from_user.full_name or message.from_user.first_name, prices, t
    )
    await message.answer(
        welcome_text, reply_markup=start_keyboard(t), parse_mode="Markdown"
    )

    resumed = await resume_flow_if_needed(message, state)
    if not resumed:
        await message.answer(
            t("messages.start_buttons_hint"),
            reply_markup=main_menu_keyboard(t),
        )
