"""Concrete repository implementations for the bot domain."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from .base import BaseRepository
from .models import (
    ActiveOrder,
    CompletedTransaction,
    Invoice,
    InvoicePayment,
    InvoiceStatus,
    User,
    UserProfile,
    UserState,
    UserStateStage,
)


class UserRepository(BaseRepository):
    async def upsert_user(self, user: User) -> None:
        query = """
        INSERT INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name
        """
        await self._execute(
            query,
            (user.user_id, user.username or "", user.full_name or ""),
            commit=True,
        )


class UserStateRepository(BaseRepository):
    async def upsert_state(self, state: UserState) -> None:
        query = """
        INSERT INTO user_states (user_id, stage, stars_count, ton_amount, wallet_address,
                                 payment_charge_id, state_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            stage=excluded.stage,
            stars_count=excluded.stars_count,
            ton_amount=excluded.ton_amount,
            wallet_address=excluded.wallet_address,
            payment_charge_id=excluded.payment_charge_id,
            state_data=excluded.state_data,
            updated=CURRENT_TIMESTAMP
        """
        payload = json.dumps(state.payload) if state.payload else None
        await self._execute(
            query,
            (
                state.user_id,
                state.stage.value,
                state.stars_count,
                state.ton_amount,
                state.wallet_address,
                state.payment_charge_id,
                payload,
            ),
            commit=True,
        )

    async def get_state(self, user_id: int) -> Optional[UserState]:
        row = await self._execute(
            "SELECT * FROM user_states WHERE user_id = ?",
            (user_id,),
            fetchone=True,
        )
        if not row:
            return None
        payload = json.loads(row["state_data"]) if row["state_data"] else None
        stage = UserStateStage(row["stage"])
        return UserState(
            user_id=row["user_id"],
            stage=stage,
            stars_count=row["stars_count"],
            ton_amount=row["ton_amount"],
            wallet_address=row["wallet_address"],
            payment_charge_id=row["payment_charge_id"],
            payload=payload,
            updated=datetime.fromisoformat(row["updated"]) if row["updated"] else None,
        )

    async def clear_state(self, user_id: int) -> None:
        await self._execute(
            "DELETE FROM user_states WHERE user_id = ?",
            (user_id,),
            commit=True,
        )


class ActiveOrderRepository(BaseRepository):
    async def delete_by_user(self, user_id: int) -> None:
        await self._execute(
            "DELETE FROM active_orders WHERE user_id = ?",
            (user_id,),
            commit=True,
        )

    async def create_order(self, order: ActiveOrder) -> ActiveOrder:
        await self.delete_by_user(order.user_id)
        query = """
        INSERT INTO active_orders (user_id, stars_count, ton_amount, wallet_address, payment_charge_id, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = await self._execute(
            query,
            (
                order.user_id,
                order.stars_count,
                order.ton_amount,
                order.wallet_address,
                order.payment_charge_id,
                order.status,
            ),
            commit=True,
        )
        order_id = cursor.lastrowid
        return ActiveOrder(
            id=order_id,
            user_id=order.user_id,
            stars_count=order.stars_count,
            ton_amount=order.ton_amount,
            wallet_address=order.wallet_address,
            payment_charge_id=order.payment_charge_id,
            status=order.status,
            created=datetime.utcnow(),
        )

    async def get_by_user(self, user_id: int) -> Optional[ActiveOrder]:
        row = await self._execute(
            "SELECT * FROM active_orders WHERE user_id = ?",
            (user_id,),
            fetchone=True,
        )
        if not row:
            return None
        return ActiveOrder(
            id=row["id"],
            user_id=row["user_id"],
            stars_count=row["stars_count"],
            ton_amount=row["ton_amount"],
            wallet_address=row["wallet_address"],
            payment_charge_id=row["payment_charge_id"],
            status=row["status"],
            created=datetime.fromisoformat(row["created"]) if row["created"] else None,
        )


class CompletedTransactionRepository(BaseRepository):
    async def record_transaction(self, transaction: CompletedTransaction) -> None:
        query = """
        INSERT INTO completed_transactions (
            user_id, tx_hash, stars_count, ton_amount, wallet_address, payment_charge_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        await self._execute(
            query,
            (
                transaction.user_id,
                transaction.tx_hash,
                transaction.stars_count,
                transaction.ton_amount,
                transaction.wallet_address,
                transaction.payment_charge_id,
                transaction.status,
            ),
            commit=True,
        )

    async def get_recent_for_user(
        self, user_id: int, limit: int = 10
    ) -> List[CompletedTransaction]:
        rows = await self._execute(
            """
            SELECT * FROM completed_transactions
            WHERE user_id = ?
            ORDER BY created DESC
            LIMIT ?
            """,
            (user_id, limit),
            fetchall=True,
        )
        transactions: List[CompletedTransaction] = []
        for row in rows or []:
            transactions.append(
                CompletedTransaction(
                    id=row["id"],
                    user_id=row["user_id"],
                    tx_hash=row["tx_hash"],
                    stars_count=row["stars_count"],
                    ton_amount=row["ton_amount"],
                    wallet_address=row["wallet_address"],
                    payment_charge_id=row["payment_charge_id"],
                    status=row["status"],
                    created=datetime.fromisoformat(row["created"]) if row["created"] else None,
                    completed_at=
                    datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                )
            )
        return transactions


class UserProfileRepository(BaseRepository):
    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        row = await self._execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,),
            fetchone=True,
        )
        if not row:
            return None
        return UserProfile(
            user_id=row["user_id"],
            primary_wallet_address=row["primary_wallet_address"],
            language=row["language"],
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row["updated_at"]
            else None,
        )

    async def ensure_profile(self, user_id: int, default_language: str) -> None:
        await self._execute(
            """
            INSERT OR IGNORE INTO user_profiles (user_id, language)
            VALUES (?, ?)
            """,
            (user_id, default_language),
            commit=True,
        )

    async def upsert_profile(self, profile: UserProfile) -> None:
        await self._execute(
            """
            INSERT INTO user_profiles (user_id, primary_wallet_address, language)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                primary_wallet_address=excluded.primary_wallet_address,
                language=excluded.language,
                updated_at=CURRENT_TIMESTAMP
            """,
            (profile.user_id, profile.primary_wallet_address, profile.language),
            commit=True,
        )

    async def upsert_partial(
        self,
        user_id: int,
        *,
        primary_wallet_address: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None:
        await self._execute(
            """
            INSERT INTO user_profiles (user_id, primary_wallet_address, language)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                primary_wallet_address = CASE
                    WHEN excluded.primary_wallet_address IS NOT NULL THEN excluded.primary_wallet_address
                    ELSE user_profiles.primary_wallet_address
                END,
                language = CASE
                    WHEN excluded.language IS NOT NULL THEN excluded.language
                    ELSE user_profiles.language
                END,
                updated_at=CURRENT_TIMESTAMP
            """,
            (user_id, primary_wallet_address, language),
            commit=True,
        )


class InvoiceRepository(BaseRepository):
    async def create_invoice(self, invoice: Invoice) -> Invoice:
        cursor = await self._execute(
            """
            INSERT INTO invoices (
                code, creator_id, payer_user_id, wallet_address, reason,
                stars_count, usd_value, ton_value, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice.code,
                invoice.creator_id,
                invoice.payer_user_id,
                invoice.wallet_address,
                invoice.reason,
                invoice.stars_count,
                invoice.usd_value,
                invoice.ton_value,
                invoice.status.value,
            ),
            commit=True,
        )
        now = datetime.now(timezone.utc)
        return Invoice(
            id=cursor.lastrowid,
            code=invoice.code,
            creator_id=invoice.creator_id,
            payer_user_id=invoice.payer_user_id,
            wallet_address=invoice.wallet_address,
            reason=invoice.reason,
            stars_count=invoice.stars_count,
            usd_value=invoice.usd_value,
            ton_value=invoice.ton_value,
            status=invoice.status,
            created_at=now,
            updated_at=now,
        )

    async def get_by_code(self, code: str) -> Optional[Invoice]:
        row = await self._execute(
            "SELECT * FROM invoices WHERE code = ?",
            (code,),
            fetchone=True,
        )
        if not row:
            return None
        return self._row_to_invoice(row)

    async def update_status(self, invoice_id: int, status: InvoiceStatus) -> None:
        await self._execute(
            """
            UPDATE invoices
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status.value, invoice_id),
            commit=True,
        )

    def _row_to_invoice(self, row) -> Invoice:
        return Invoice(
            id=row["id"],
            code=row["code"],
            creator_id=row["creator_id"],
            payer_user_id=row["payer_user_id"],
            wallet_address=row["wallet_address"],
            reason=row["reason"],
            stars_count=row["stars_count"],
            usd_value=row["usd_value"],
            ton_value=row["ton_value"],
            status=InvoiceStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else None,
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row["updated_at"]
            else None,
        )


class InvoicePaymentRepository(BaseRepository):
    async def record_payment(self, payment: InvoicePayment) -> InvoicePayment:
        cursor = await self._execute(
            """
            INSERT INTO invoice_payments (
                invoice_id, payer_id, stars_paid, ton_value,
                payment_charge_id, tx_hash
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payment.invoice_id,
                payment.payer_id,
                payment.stars_paid,
                payment.ton_value,
                payment.payment_charge_id,
                payment.tx_hash,
            ),
            commit=True,
        )
        return InvoicePayment(
            id=cursor.lastrowid,
            invoice_id=payment.invoice_id,
            payer_id=payment.payer_id,
            stars_paid=payment.stars_paid,
            ton_value=payment.ton_value,
            payment_charge_id=payment.payment_charge_id,
            tx_hash=payment.tx_hash,
            paid_at=datetime.now(timezone.utc),
        )
