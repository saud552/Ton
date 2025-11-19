"""Service module for creating and managing invoices."""

from __future__ import annotations

import secrets
from typing import Optional

from app.db import Invoice, InvoiceRepository, InvoiceStatus


class InvoiceService:
    def __init__(self, repo: InvoiceRepository):
        self._repo = repo

    async def create_invoice(
        self,
        creator_id: int,
        payer_user_id: Optional[int],
        wallet_address: str,
        reason: str,
        stars_count: int,
        star_price_usd: float,
        star_price_ton: float,
    ) -> Invoice:
        code = await self._generate_unique_code(creator_id)
        usd_value = stars_count * star_price_usd
        ton_value = stars_count * star_price_ton
        invoice = Invoice(
            id=None,
            code=code,
            creator_id=creator_id,
            payer_user_id=payer_user_id,
            wallet_address=wallet_address,
            reason=reason,
            stars_count=stars_count,
            usd_value=usd_value,
            ton_value=ton_value,
            status=InvoiceStatus.PENDING,
            created_at=None,
            updated_at=None,
        )
        return await self._repo.create_invoice(invoice)

    async def _generate_unique_code(self, creator_id: int) -> str:
        for _ in range(5):
            token = secrets.token_hex(2).upper()
            code = f"StarsPro-{creator_id}/{token}"
            existing = await self._repo.get_by_code(code)
            if not existing:
                return code
        raise RuntimeError("Unable to generate unique invoice code")

    async def get_invoice(self, code: str) -> Optional[Invoice]:
        return await self._repo.get_by_code(code)


__all__ = ["InvoiceService"]
