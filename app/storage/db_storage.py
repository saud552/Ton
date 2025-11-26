"""Database-backed FSM storage using the UserState repository."""

from __future__ import annotations

from typing import Any, Dict, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

from app.db import (
    DatabaseManager,
    UserProfileRepository,
    UserState,
    UserStateRepository,
    UserStateStage,
)


class DatabaseStorage(BaseStorage):
    """Persist FSM state and data inside the existing user_states table."""

    def __init__(self, manager: DatabaseManager, default_language: str = "ar"):
        self._manager = manager
        self._repo = UserStateRepository(manager)
        self._profile_repo = UserProfileRepository(manager)
        self._default_language = default_language

    async def close(self) -> None:
        # Nothing to close explicitly because connections are created per operation
        return None

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        record = await self._get_or_create(key)
        state_value = self._normalize_state(state)
        if state_value:
            try:
                record.stage = UserStateStage(state_value)
            except ValueError:
                record.stage = UserStateStage.IDLE
        else:
            record.stage = UserStateStage.IDLE
        await self._repo.upsert_state(record)

    async def get_state(self, key: StorageKey) -> Optional[str]:
        record = await self._repo.get_state(key.user_id)
        if not record or record.stage == UserStateStage.IDLE:
            return None
        return record.stage.value

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        record = await self._get_or_create(key)
        payload = data or {}
        record.payload = payload
        record.stars_count = payload.get("stars_count")
        record.ton_amount = payload.get("ton_amount")
        record.wallet_address = payload.get("wallet_address")
        record.payment_charge_id = payload.get("payment_charge_id")
        await self._repo.upsert_state(record)
        await self._sync_profile_from_payload(key.user_id, payload)

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        record = await self._repo.get_state(key.user_id)
        if not record or not record.payload:
            return {}
        return dict(record.payload)

    async def _get_or_create(self, key: StorageKey) -> UserState:
        record = await self._repo.get_state(key.user_id)
        if record:
            return record
        new_record = UserState(user_id=key.user_id)
        await self._repo.upsert_state(new_record)
        await self._profile_repo.ensure_profile(
            key.user_id, default_language=self._default_language
        )
        return new_record

    def _normalize_state(self, state: StateType) -> Optional[str]:
        if state is None:
            return None
        if isinstance(state, State):
            return state.state
        return str(state)

    async def _sync_profile_from_payload(
        self, user_id: int, payload: Dict[str, Any]
    ) -> None:
        language = payload.get("preferred_language")
        wallet = payload.get("primary_wallet_address")
        if language is None and wallet is None:
            return
        await self._profile_repo.upsert_partial(
            user_id, primary_wallet_address=wallet, language=language
        )


__all__ = ["DatabaseStorage"]
