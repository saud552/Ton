"""Base repository implementation with shared helpers."""

from __future__ import annotations

from typing import Any, Iterable

from .manager import DatabaseManager


class BaseRepository:
    """Provide shared query execution helpers for repositories."""

    def __init__(self, manager: DatabaseManager):
        self._manager = manager

    async def _execute(
        self,
        query: str,
        params: Iterable[Any] | None = None,
        *,
        fetchone: bool = False,
        fetchall: bool = False,
        commit: bool = False,
    ):
        params = tuple(params or [])
        async with self._manager.acquire() as conn:
            cursor = await conn.execute(query, params)
            if commit:
                await conn.commit()
            if fetchone:
                return await cursor.fetchone()
            if fetchall:
                return await cursor.fetchall()
            return cursor
