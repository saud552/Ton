"""Centralized logging configuration with rotating file handlers."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict

from .settings import AppSettings


def configure_logging(settings: AppSettings) -> None:
    """Configure console and file handlers according to the active settings."""

    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    error_log_path = log_path.parent / "errors.log"

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "standard",
            },
            "info_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": "standard",
                "filename": str(log_path),
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "standard",
                "filename": str(error_log_path),
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "info_file", "error_file"],
        },
    }

    logging.config.dictConfig(logging_config)
    logging.getLogger(__name__).debug(
        "Logging configured", extra={"env": settings.environment.value}
    )
