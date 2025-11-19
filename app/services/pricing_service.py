"""Service responsible for refreshing TON and star prices."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from app.config import AppSettings, get_settings
from .http_client import HttpClient


class PricingService:
    def __init__(
        self,
        settings: AppSettings,
        http_client: Optional[HttpClient] = None,
    ):
        self._settings = settings
        self._interval = max(30, settings.pricing_refresh_interval)
        self._prices: Dict[str, float] = {
            "ton_usd": settings.ton_price_usd,
            "star_usd": settings.star_price_usd,
            "star_ton": settings.star_price_ton,
        }
        self._http_client = http_client or HttpClient(settings.http_timeout)
        self._owns_client = http_client is None
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._last_refresh: Optional[datetime] = None
        self._last_error: Optional[str] = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run_loop(), name="pricing-service")

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
        if self._owns_client:
            await self._http_client.close()

    async def refresh_prices(self) -> Dict[str, float]:
        session = await self._http_client.get_session()
        url = self._settings.pricing_provider_url
        try:
            async with session.get(url) as response:
                data = await response.json()
                ton_usd = float(data.get("the-open-network", {}).get("usd", self._prices["ton_usd"]))
                star_usd = self._settings.star_price_usd
                star_ton = star_usd / ton_usd if ton_usd else self._prices["star_ton"]
                async with self._lock:
                    self._prices.update(
                        {
                            "ton_usd": ton_usd,
                            "star_usd": star_usd,
                            "star_ton": star_ton,
                        }
                    )
                    self._last_refresh = datetime.now(timezone.utc)
                    self._last_error = None
                self._logger.info("Pricing refreshed: TON %.4f USD", ton_usd)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.warning("Failed to refresh pricing: %s", exc)
            self._last_error = str(exc)
        return await self.get_prices()

    async def get_prices(self) -> Dict[str, float]:
        async with self._lock:
            return dict(self._prices)

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            await self.refresh_prices()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                continue

    async def get_status(self) -> Dict[str, Optional[str]]:
        async with self._lock:
            return {
                "running": str(bool(self._task and not self._task.done())),
                "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
                "last_error": self._last_error,
                "ton_usd": f"{self._prices['ton_usd']:.4f}",
                "star_ton": f"{self._prices['star_ton']:.6f}",
            }


def build_pricing_service(http_client: Optional[HttpClient] = None) -> PricingService:
    settings = get_settings()
    return PricingService(settings, http_client=http_client)


__all__ = ["PricingService", "build_pricing_service"]
