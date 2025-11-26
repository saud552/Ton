import pytest

from app.db import DatabaseManager, InvoiceRepository, User, UserRepository
from app.services import InvoiceService


@pytest.mark.asyncio
async def test_invoice_service_creates_unique_codes(tmp_path):
    db_path = tmp_path / "invoice_service.db"
    manager = DatabaseManager(str(db_path))
    await manager.initialize()

    user_repo = UserRepository(manager)
    await user_repo.upsert_user(User(user_id=100, username="creator", full_name="Creator"))
    await user_repo.upsert_user(User(user_id=200, username="payer", full_name="Payer"))

    repo = InvoiceRepository(manager)
    service = InvoiceService(repo)

    invoice = await service.create_invoice(
        creator_id=100,
        payer_user_id=200,
        wallet_address="EQCREATOR",
        reason="Test",
        stars_count=250,
        star_price_usd=0.015,
        star_price_ton=0.006,
    )

    assert invoice.code.startswith("StarsPro-100/")
    assert invoice.stars_count == 250
    assert pytest.approx(invoice.usd_value, rel=1e-9) == 3.75
    assert pytest.approx(invoice.ton_value, rel=1e-9) == 1.5
