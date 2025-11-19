"""Periodic monitor for the bot's TON balance."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.config import AppSettings, get_settings
from .ton_gateway import TonGateway


class BalanceMonitor:
    def __init__(
        self,
        ton_gateway: TonGateway,
        settings: AppSettings,
    ):
        self._gateway = ton_gateway
        self._settings = settings
        self._interval = max(30, settings.balance_refresh_interval)
        self._latest_balance: float = 0.0
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(self.__class__.__name__)

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run_loop(), name="balance-monitor")

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def refresh_balance(self) -> float:
        success, balance = await self._gateway.get_balance()
        if success:
            async with self._lock:
                self._latest_balance = balance
            self._logger.info("Wallet balance refreshed: %.6f TON", balance)
        else:
            self._logger.warning("Failed to refresh wallet balance")
        return self._latest_balance

    async def get_latest_balance(self) -> float:
        async with self._lock:
            return self._latest_balance

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            await self.refresh_balance()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                continue


def build_balance_monitor(ton_gateway: TonGateway) -> BalanceMonitor:
    settings = get_settings()
    return BalanceMonitor(ton_gateway, settings)


__all__ = ["BalanceMonitor", "build_balance_monitor"]
