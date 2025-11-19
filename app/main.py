"""Application bootstrap entrypoint for the modular Aiogram bot."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app import AppSettings, configure_logging, get_settings
from app.context import (
    AppContext,
    BroadcastConfig,
    ForcedSubscriptionConfig,
    MaintenanceConfig,
    set_context,
)
from app.db import DatabaseManager
from app.handlers import get_routers
from app.services import (
    BalanceMonitor,
    HttpClient,
    LocalizationService,
    MetricsCollector,
    PricingService,
    TonService,
)
from app.storage import DatabaseStorage

logger = logging.getLogger("app.bootstrap")


def bootstrap() -> AppSettings:
    """Load settings and configure logging for the current environment."""

    settings = get_settings()
    configure_logging(settings)
    logger.info(
        "Bootstrap complete",
        extra={"environment": settings.environment.value},
    )
    return settings


async def run_bot() -> None:
    """Configure dependencies and start Aiogram polling."""

    settings = bootstrap()
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.MARKDOWN)

    db_manager = DatabaseManager(settings.database_file)
    await db_manager.initialize()

    ton_http_client = HttpClient(settings.http_timeout)
    pricing_http_client = HttpClient(settings.http_timeout)

    localization = LocalizationService(
        Path(__file__).resolve().parent / "locales",
        default_language=settings.default_user_language,
    )
    ton_gateway = TonService(settings, http_client=ton_http_client)
    pricing_service = PricingService(settings, http_client=pricing_http_client)
    balance_monitor = BalanceMonitor(ton_gateway, settings)
    metrics = MetricsCollector()

    storage = DatabaseStorage(
        db_manager, default_language=settings.default_user_language
    )
    dispatcher = Dispatcher(storage=storage)

    for router in get_routers():
        dispatcher.include_router(router)

    set_context(
        AppContext(
            settings=settings,
            db_manager=db_manager,
            ton_gateway=ton_gateway,
            pricing_service=pricing_service,
            balance_monitor=balance_monitor,
            metrics=metrics,
            localization=localization,
            maintenance=MaintenanceConfig(
                enabled=settings.maintenance_mode,
                message=settings.maintenance_message,
            ),
            forced_subscription=ForcedSubscriptionConfig(
                enabled=settings.forced_subscription_enabled,
                channels=settings.forced_subscription_channels,
            ),
            broadcast=BroadcastConfig(
                batch_size=settings.broadcast_batch_size,
                delay_seconds=settings.broadcast_delay_seconds,
            ),
        )
    )

    await pricing_service.start()
    await balance_monitor.start()

    try:
        await dispatcher.start_polling(bot)
    finally:
        with suppress(Exception):
            await storage.close()
        with suppress(Exception):
            await pricing_service.stop()
        with suppress(Exception):
            await balance_monitor.stop()
        with suppress(Exception):
            await ton_gateway.close()
        with suppress(Exception):
            await ton_http_client.close()
        with suppress(Exception):
            await pricing_http_client.close()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
