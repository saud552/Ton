"""Utilities for handling forced subscription logic."""

from __future__ import annotations

from typing import List, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.context import ForcedSubscriptionConfig


async def check_subscription(
    bot: Bot, user_id: int, config: ForcedSubscriptionConfig
) -> Tuple[bool, List[str]]:
    if not config.enabled or not config.channels:
        return True, []

    missing: List[str] = []
    for channel in config.channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in {"left", "kicked"}:
                missing.append(channel)
        except TelegramBadRequest:
            missing.append(channel)
    return len(missing) == 0, missing


__all__ = ["check_subscription"]
