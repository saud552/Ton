import logging
from typing import Optional, Tuple

from app import get_settings
from app.services import HttpClient, TonGateway, TonService

logger = logging.getLogger(__name__)


class TONHandler:
    """واجهة عالية المستوى مبنية على TonGateway لتوافق TeleBot الحالي."""

    def __init__(self, gateway: TonGateway):
        self._gateway = gateway

    async def send_ton(self, recipient_address: str, amount_ton: float) -> Tuple[bool, str]:
        if not await self._gateway.validate_address(recipient_address):
            return False, "عنوان المحفظة غير صحيح"

        success, balance = await self._gateway.get_balance()
        if not success:
            return False, "فشل في التحقق من رصيد المحفظة"
        if balance < amount_ton:
            return False, f"رصيد غير كافٍ. الرصيد الحالي: {balance:.6f} TON"
        return await self._gateway.send_ton(recipient_address, amount_ton)

    async def get_balance(self, address: Optional[str] = None) -> Tuple[bool, float]:
        return await self._gateway.get_balance(address)

    async def validate_address(self, address: str) -> bool:
        return await self._gateway.validate_address(address)

    async def get_transaction_info(self, tx_hash: str):
        return await self._gateway.get_transaction_info(tx_hash)

    async def shutdown(self) -> None:
        close_coro = getattr(self._gateway, "close", None)
        if close_coro:
            await close_coro()


_settings = get_settings()
_http_client = HttpClient(_settings.http_timeout)
_ton_service = TonService(_settings, http_client=_http_client)
ton_handler = TONHandler(_ton_service)