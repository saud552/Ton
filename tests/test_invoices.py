import pytest

from app.db import (
    DatabaseManager,
    Invoice,
    InvoicePayment,
    InvoicePaymentRepository,
    InvoiceRepository,
    InvoiceStatus,
    User,
    UserRepository,
)


@pytest.mark.asyncio
async def test_invoice_lifecycle(tmp_path):
    db_path = tmp_path / "invoices.db"
    manager = DatabaseManager(str(db_path))
    await manager.initialize()

    user_repo = UserRepository(manager)
    await user_repo.upsert_user(User(user_id=1, username="creator", full_name="Creator"))
    await user_repo.upsert_user(User(user_id=2, username="payer", full_name="Payer"))

    invoice_repo = InvoiceRepository(manager)
    payment_repo = InvoicePaymentRepository(manager)

    invoice = await invoice_repo.create_invoice(
        Invoice(
            id=None,
            code="StarsPro-1/ABC123",
            creator_id=1,
            payer_user_id=2,
            wallet_address="EQCREATOR",
            reason="Test payment",
            stars_count=150,
            usd_value=10.5,
            ton_value=1.2,
            status=InvoiceStatus.PENDING,
            created_at=None,
            updated_at=None,
        )
    )

    fetched = await invoice_repo.get_by_code("StarsPro-1/ABC123")
    assert fetched is not None
    assert fetched.code == invoice.code

    await invoice_repo.update_status(invoice.id, InvoiceStatus.PAID)
    updated = await invoice_repo.get_by_code(invoice.code)
    assert updated.status == InvoiceStatus.PAID

    payment = await payment_repo.record_payment(
        InvoicePayment(
            id=None,
            invoice_id=invoice.id,
            payer_id=2,
            stars_paid=150,
            ton_value=1.2,
            payment_charge_id="charge123",
            tx_hash="hash123",
            paid_at=None,
        )
    )
    assert payment.id is not None
