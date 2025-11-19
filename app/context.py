"""Application-wide context container for dependency sharing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.config import AppSettings
from app.db import DatabaseManager
from app.services import (
    BalanceMonitor,
    LocalizationService,
    MetricsCollector,
    PricingService,
    TonGateway,
)


@dataclass(slots=True)
class MaintenanceConfig:
    enabled: bool
    message: str


@dataclass(slots=True)
class ForcedSubscriptionConfig:
    enabled: bool
    channels: list[str]


@dataclass(slots=True)
class BroadcastConfig:
    batch_size: int
    delay_seconds: float


@dataclass(slots=True)
class AppContext:
    settings: AppSettings
    db_manager: DatabaseManager
    ton_gateway: TonGateway
    pricing_service: PricingService
    balance_monitor: BalanceMonitor
    metrics: MetricsCollector
    localization: LocalizationService
    maintenance: MaintenanceConfig
    forced_subscription: ForcedSubscriptionConfig
    broadcast: BroadcastConfig


_context: Optional[AppContext] = None


def set_context(context: AppContext) -> None:
    global _context
    _context = context


def get_context() -> AppContext:
    if _context is None:
        raise RuntimeError("Application context is not initialized")
    return _context


__all__ = [
    "AppContext",
    "MaintenanceConfig",
    "ForcedSubscriptionConfig",
    "BroadcastConfig",
    "set_context",
    "get_context",
]
