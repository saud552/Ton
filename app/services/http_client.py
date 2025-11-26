"""Shared aiohttp client session manager."""

from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp


class HttpClient:
    """Manage a shared aiohttp session with configurable timeout."""

    def __init__(self, timeout: float = 10.0):
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        async with self._lock:
            if self._session and not self._session.closed:
                return self._session
            self._session = aiohttp.ClientSession(timeout=self._timeout)
            return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def is_closed(self) -> bool:
        return self._session is None or self._session.closed


__all__ = ["HttpClient"]
