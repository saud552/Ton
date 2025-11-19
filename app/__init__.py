"""Core application package providing modular bot infrastructure."""

from app.config import get_settings  # re-export for convenience

__all__ = ["get_settings"]
