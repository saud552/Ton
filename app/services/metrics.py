"""Simple in-memory metrics collector for operational monitoring."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict


class MetricsCollector:
    """Thread-safe counter aggregation for runtime metrics."""

    def __init__(self) -> None:
        self._counters: Dict[str, int] = defaultdict(int)
        self._last_events: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        self._default_time = datetime.min.replace(tzinfo=timezone.utc)

    async def increment(self, name: str, amount: int = 1) -> None:
        async with self._lock:
            self._counters[name] += amount
            self._last_events[name] = datetime.now(timezone.utc)

    async def snapshot(self) -> Dict[str, Dict[str, str]]:
        async with self._lock:
            return {
                name: {
                    "count": str(value),
                    "last_event": self._last_events.get(name, self._default_time).isoformat(),
                }
                for name, value in self._counters.items()
            }


__all__ = ["MetricsCollector"]
