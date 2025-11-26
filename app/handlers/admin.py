"""Admin monitoring commands."""

from __future__ import annotations

from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Router

from app.context import get_context

router = Router(name="admin")


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    ctx = get_context()
    user_id = message.from_user.id
    if user_id not in ctx.settings.admin_user_ids:
        await message.answer("🚫 لا تمتلك صلاحية الوصول إلى لوحة الإدارة.")
        return

    balance_status = await ctx.balance_monitor.get_status()
    pricing_status = await ctx.pricing_service.get_status()
    metrics_snapshot = await ctx.metrics.snapshot()

    summary_lines = [
        "🛠️ **لوحة المراقبة**",
        f"👤 المشرف: `{user_id}`",
        f"🌐 البيئة: {ctx.settings.environment.value}",
        "\n**الرصيد**:",
        f"- آخر تحديث: {balance_status['last_refresh']}",
        f"- الرصيد الحالي: {balance_status['latest_balance']} TON",
        f"- حالة المهمة: {balance_status['running']}",
        f"- آخر خطأ: {balance_status['last_error']}",
        "\n**الأسعار**:",
        f"- آخر تحديث: {pricing_status['last_refresh']}",
        f"- TON/USD: {pricing_status['ton_usd']}",
        f"- Star/TON: {pricing_status['star_ton']}",
        f"- حالة المهمة: {pricing_status['running']}",
        f"- آخر خطأ: {pricing_status['last_error']}",
        "\n**المقاييس**:",
    ]

    if not metrics_snapshot:
        summary_lines.append("- لا توجد أخطاء مسجلة")
    else:
        for name, payload in metrics_snapshot.items():
            summary_lines.append(
                f"- {name}: {payload['count']} (آخر حدث: {payload['last_event']})"
            )

    await message.answer("\n".join(summary_lines), parse_mode="Markdown")
