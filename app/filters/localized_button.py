"""Filter that matches reply button text in the user's language."""

from __future__ import annotations

from aiogram.filters import Filter
from aiogram.types import Message

from app.handlers.utils import resolve_language_tooling


class LocalizedButton(Filter):
    def __init__(self, key: str):
        self._key = key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        _, t = await resolve_language_tooling(message.from_user.id)
        return message.text.strip() == t(f"buttons.{self._key}")


__all__ = ["LocalizedButton"]
