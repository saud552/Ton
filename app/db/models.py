"""Data models and enums for the persistence layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class UserStateStage(str, Enum):
    """Business stages persisted for resuming workflows."""

    IDLE = "idle"
    WAITING_FOR_STARS = "waiting_for_stars"
    WAITING_FOR_PAYMENT = "waiting_for_payment"
    WAITING_FOR_WALLET = "waiting_for_wallet"
    CONFIRMING_WALLET = "confirming_wallet"


@dataclass(slots=True)
class User:
    user_id: int
    username: Optional[str]
    full_name: Optional[str]
    created: Optional[datetime] = None


@dataclass(slots=True)
class UserState:
    user_id: int
    stage: UserStateStage = UserStateStage.IDLE
    stars_count: Optional[int] = None
    ton_amount: Optional[float] = None
    wallet_address: Optional[str] = None
    payment_charge_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    updated: Optional[datetime] = None


@dataclass(slots=True)
class ActiveOrder:
    id: Optional[int]
    user_id: int
    stars_count: int
    ton_amount: float
    wallet_address: str
    payment_charge_id: Optional[str]
    status: str
    created: Optional[datetime]


@dataclass(slots=True)
class CompletedTransaction:
    id: Optional[int]
    user_id: int
    tx_hash: str
    stars_count: int
    ton_amount: float
    wallet_address: str
    payment_charge_id: Optional[str]
    status: str
    created: Optional[datetime]
    completed_at: Optional[datetime]


__all__ = [
    "User",
    "UserState",
    "UserStateStage",
    "ActiveOrder",
    "CompletedTransaction",
]
