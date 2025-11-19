"""Router displaying recent transactions."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.context import get_context
from app.db import CompletedTransactionRepository
from app.keyboards.common import Buttons, main_menu_keyboard

router = Router(name="history")


@router.message(F.text == Buttons.TRANSACTION_HISTORY)
async def show_history(message: Message) -> None:
    ctx = get_context()
    tx_repo = CompletedTransactionRepository(ctx.db_manager)
    transactions = await tx_repo.get_recent_for_user(message.from_user.id, limit=5)

    if not transactions:
        await message.answer(
            "📊 **سجل المعاملات**\n\nلا توجد معاملات سابقة.",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    history_text = "📊 **سجل المعاملات الأخيرة**\n\n"
    for idx, tx in enumerate(transactions, start=1):
        short_hash = tx.tx_hash[:8] + "..." + tx.tx_hash[-8:] if len(tx.tx_hash) > 16 else tx.tx_hash
        short_wallet = (
            tx.wallet_address[:8] + "..." + tx.wallet_address[-8:]
            if len(tx.wallet_address) > 16
            else tx.wallet_address
        )
        created = tx.created.strftime("%Y-%m-%d") if tx.created else "-"
        history_text += (
            f"{idx}. ⭐ {tx.stars_count} → 💰 {tx.ton_amount:.6f} TON\n"
            f"   📍 {short_wallet}\n"
            f"   🔗 {short_hash}\n"
            f"   📅 {created}\n\n"
        )

    await message.answer(history_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
