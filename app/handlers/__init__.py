"""Message and callback handlers for the bot."""

from aiogram import Router

from . import (
    admin,
    common,
    history,
    invoice_creation,
    payments,
    selling,
    settings,
    start,
    wallet,
)


def get_routers() -> list[Router]:
    """Return routers ordered by priority."""

    return [
        start.router,
        selling.router,
        invoice_creation.router,
        payments.router,
        wallet.router,
        settings.router,
        history.router,
        admin.router,
        common.router,
    ]


__all__ = ["get_routers"]
