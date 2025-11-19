"""Concrete TON Center gateway implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

import aiohttp

from app.config import AppSettings, get_settings
from .http_client import HttpClient
from .ton_gateway import TonGateway, TransactionInfo


class TonServiceError(Exception):
    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.payload = payload or {}


class TonService(TonGateway):
    def __init__(
        self,
        settings: AppSettings,
        http_client: Optional[HttpClient] = None,
    ):
        self._settings = settings
        self._api_key = settings.ton_api_key
        self._api_base_url = settings.api_base_url.rstrip("/")
        self._http_client = http_client or HttpClient(settings.http_timeout)
        self._owns_client = http_client is None
        self._max_retries = max(1, settings.ton_max_retries)
        self._logger = logging.getLogger(self.__class__.__name__)

    async def close(self) -> None:
        if self._owns_client:
            await self._http_client.close()

    async def send_ton(self, recipient_address: str, amount_ton: float) -> Tuple[bool, str]:
        payload = {
            "secretKey": self._settings.wallet_private_key,
            "to": recipient_address,
            "amount": int(amount_ton * 1e9),
            "message": "Payment for Telegram Stars",
        }
        try:
            data = await self._request("POST", "sendTransaction", json=payload)
            if data.get("ok"):
                tx_hash = data["result"]["hash"]
                self._logger.info("Sent %.6f TON to %s", amount_ton, recipient_address)
                return True, tx_hash
            return False, data.get("error", "Unknown error")
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Send TON failed: %s", exc)
            return False, str(exc)

    async def get_balance(self, address: Optional[str] = None) -> Tuple[bool, float]:
        address = address or self._settings.deposit_address
        params = {"address": address}
        try:
            data = await self._request("GET", "getAddressBalance", params=params)
            if data.get("ok"):
                balance_nano = int(data["result"])
                return True, balance_nano / 1e9
            return False, 0.0
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Get balance failed: %s", exc)
            return False, 0.0

    async def validate_address(self, address: str) -> bool:
        params = {"address": address}
        try:
            data = await self._request("GET", "validateAddress", params=params)
            return data.get("ok", False) and data.get("result", {}).get("valid", False)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Validate address failed: %s", exc)
            return False

    async def get_transaction_info(self, tx_hash: str) -> Tuple[bool, Optional[TransactionInfo]]:
        params = {"hash": tx_hash, "limit": 1}
        try:
            data = await self._request("GET", "getTransactions", params=params)
            if data.get("ok") and data.get("result"):
                payload = data["result"][0]
                info = TransactionInfo(
                    hash=payload.get("transaction_id", {}).get("hash", tx_hash),
                    amount=float(payload.get("in_msg", {}).get("value", 0)) / 1e9,
                    to_address=payload.get("in_msg", {}).get("destination", ""),
                    raw=payload,
                )
                return True, info
            return False, None
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Get transaction info failed: %s", exc)
            return False, None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        params = kwargs.pop("params", {})
        params["api_key"] = self._api_key
        url = f"{self._api_base_url}/{endpoint}"
        backoff = 0.5
        for attempt in range(1, self._max_retries + 1):
            try:
                session = await self._http_client.get_session()
                async with session.request(method, url, params=params, **kwargs) as response:
                    data = await response.json(content_type=None)
                    if response.status == 200:
                        return data
                    raise TonServiceError(f"HTTP {response.status}", data)
            except (aiohttp.ClientError, asyncio.TimeoutError, TonServiceError) as exc:
                if attempt == self._max_retries:
                    raise
                self._logger.warning("TON request failed (%s/%s): %s", attempt, self._max_retries, exc)
                await asyncio.sleep(backoff)
                backoff *= 2
        raise TonServiceError("Max retries exceeded")


def build_ton_service() -> TonService:
    settings = get_settings()
    return TonService(settings)


__all__ = ["TonService", "TonServiceError", "build_ton_service"]
