"""Application bootstrap entrypoint for the modular bot."""

from __future__ import annotations

import logging

from app import AppSettings, configure_logging, get_settings


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


if __name__ == "__main__":
    bootstrap()
