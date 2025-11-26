import asyncio
import logging
from typing import List, Optional

from app.db import (
    ActiveOrder,
    ActiveOrderRepository,
    CompletedTransaction,
    CompletedTransactionRepository,
    DatabaseManager,
    User,
    UserRepository,
    UserState,
    UserStateRepository,
    UserStateStage,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """واجهة متزامنة مبنية على طبقة DAO غير المتزامنة."""

    def __init__(self, db_file: str):
        self._manager = DatabaseManager(db_file)
        self._run(self._manager.initialize())

    def _run(self, coroutine):
        """تنفيذ المهام غير المتزامنة داخل السياق المتزامن الحالي."""

        return asyncio.run(coroutine)

    def add_user(self, user_id: int, username: Optional[str], full_name: Optional[str]) -> None:
        logger.debug("Adding/updating user %s", user_id)
        self._run(
            UserRepository(self._manager).upsert_user(
                User(user_id=user_id, username=username, full_name=full_name)
            )
        )

    def set_user_state(
        self,
        user_id: int,
        stage: UserStateStage,
        *,
        stars_count: Optional[int] = None,
        ton_amount: Optional[float] = None,
        wallet_address: Optional[str] = None,
        payment_charge_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        state = UserState(
            user_id=user_id,
            stage=stage,
            stars_count=stars_count,
            ton_amount=ton_amount,
            wallet_address=wallet_address,
            payment_charge_id=payment_charge_id,
            payload=payload,
        )
        self._run(UserStateRepository(self._manager).upsert_state(state))

    def get_user_state(self, user_id: int) -> Optional[UserState]:
        return self._run(UserStateRepository(self._manager).get_state(user_id))

    def clear_user_state(self, user_id: int) -> None:
        self.set_user_state(user_id, UserStateStage.IDLE)

    def create_order(
        self,
        user_id: int,
        stars_count: int,
        ton_amount: float,
        wallet_address: str,
        payment_charge_id: Optional[str] = None,
    ) -> bool:
        order = ActiveOrder(
            id=None,
            user_id=user_id,
            stars_count=stars_count,
            ton_amount=ton_amount,
            wallet_address=wallet_address,
            payment_charge_id=payment_charge_id,
            status="pending",
            created=None,
        )
        created = self._run(ActiveOrderRepository(self._manager).create_order(order))
        logger.info("Order created for user %s (#%s)", user_id, created.id)
        return True

    def get_order(self, user_id: int) -> Optional[ActiveOrder]:
        return self._run(ActiveOrderRepository(self._manager).get_by_user(user_id))

    def complete_order(self, user_id: int, tx_hash: str) -> bool:
        order = self.get_order(user_id)
        if not order:
            return False

        transaction = CompletedTransaction(
            id=None,
            user_id=user_id,
            tx_hash=tx_hash,
            stars_count=order.stars_count,
            ton_amount=order.ton_amount,
            wallet_address=order.wallet_address,
            payment_charge_id=order.payment_charge_id,
            status="completed",
            created=None,
            completed_at=None,
        )
        self._run(
            CompletedTransactionRepository(self._manager).record_transaction(transaction)
        )
        self._run(ActiveOrderRepository(self._manager).delete_by_user(user_id))
        self.clear_user_state(user_id)
        logger.info("Order completed for user %s, tx %s", user_id, tx_hash)
        return True

    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[CompletedTransaction]:
        return self._run(
            CompletedTransactionRepository(self._manager).get_recent_for_user(user_id, limit)
        )


import config

db = DatabaseService(config.DATABASE_FILE)