import pytest

from app.services.metrics import MetricsCollector


@pytest.mark.asyncio
async def test_metrics_increment_and_snapshot():
    metrics = MetricsCollector()
    await metrics.increment("ton_transfer_failed")
    await metrics.increment("ton_transfer_failed")
    snapshot = await metrics.snapshot()
    assert snapshot["ton_transfer_failed"]["count"] == "2"
    assert "last_event" in snapshot["ton_transfer_failed"]
