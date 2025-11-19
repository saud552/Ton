"""Concrete repository implementations for the bot domain."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from .base import BaseRepository
from .models import (
    ActiveOrder,
    CompletedTransaction,
    User,
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
