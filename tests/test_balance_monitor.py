import pytest

from app.config import get_settings
from app.services import BalanceMonitor, MockTonGateway


@pytest.mark.asyncio
async def test_balance_monitor_refresh_updates_state():
    settings = get_settings()
    monitor = BalanceMonitor(MockTonGateway(initial_balance=7.5), settings)
    balance = await monitor.refresh_balance()
    assert abs(balance - 7.5) < 1e-9
    status = await monitor.get_status()
    assert status["latest_balance"] == "7.500000"
