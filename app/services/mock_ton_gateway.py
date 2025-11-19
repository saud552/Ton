"""Testing stub for TonGateway implementations."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .ton_gateway import TonGateway, TransactionInfo


class MockTonGateway(TonGateway):
    def __init__(self, initial_balance: float = 10.0):
        self.balance = initial_balance
        self.sent_transactions: Dict[str, float] = {}

    async def send_ton(self, recipient_address: str, amount_ton: float) -> Tuple[bool, str]:
        if amount_ton > self.balance:
            return False, "Insufficient funds"
        self.balance -= amount_ton
        tx_hash = f"mock-{len(self.sent_transactions) + 1}"
        self.sent_transactions[tx_hash] = amount_ton
        return True, tx_hash

    async def get_balance(self, address: Optional[str] = None) -> Tuple[bool, float]:
        return True, self.balance

    async def validate_address(self, address: str) -> bool:
        return address.startswith(("EQ", "UQ", "0Q"))

    async def get_transaction_info(self, tx_hash: str):
        amount = self.sent_transactions.get(tx_hash)
        if amount is None:
            return False, None
        info = TransactionInfo(hash=tx_hash, amount=amount, to_address="mock", raw={})
        return True, info


__all__ = ["MockTonGateway"]
