"""TON gateway protocol and shared DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Tuple


@dataclass(slots=True)
class TransactionInfo:
    hash: str
    amount: float
    to_address: str
    raw: Dict[str, Any]


class TonGateway(Protocol):
    async def send_ton(self, recipient_address: str, amount_ton: float) -> Tuple[bool, str]:
        ...

    async def get_balance(self, address: Optional[str] = None) -> Tuple[bool, float]:
        ...

    async def validate_address(self, address: str) -> bool:
        ...

    async def get_transaction_info(self, tx_hash: str) -> Tuple[bool, Optional[TransactionInfo]]:
        ...


__all__ = ["TonGateway", "TransactionInfo"]
