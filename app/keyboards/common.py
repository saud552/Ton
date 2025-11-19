"""Reusable reply keyboards for the bot."""

from __future__ import annotations

from typing import Callable

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


LocalizationFn = Callable[[str], str]


def main_menu_keyboard(t: LocalizationFn) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("buttons.sell_stars")),
                KeyboardButton(text=t("buttons.create_invoice")),
            ],
            [
                KeyboardButton(text=t("buttons.pay_invoice")),
            ],
            [
                KeyboardButton(text=t("buttons.change_wallet")),
                KeyboardButton(text=t("buttons.change_language")),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=t("messages.start_buttons_hint"),
    )


def start_keyboard(t: LocalizationFn) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("buttons.sell_stars"))]],
        resize_keyboard=True,
    )


def cancel_keyboard(t: LocalizationFn) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("buttons.cancel"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def wallet_confirmation_keyboard(t: LocalizationFn) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("buttons.confirm_address"))],
            [KeyboardButton(text=t("buttons.cancel"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def wallet_choice_keyboard(
    t: LocalizationFn, *, has_primary: bool
) -> ReplyKeyboardMarkup:
    buttons = []
    if has_primary:
        buttons.append([KeyboardButton(text=t("buttons.use_my_wallet"))])
    buttons.append([KeyboardButton(text=t("buttons.use_new_wallet"))])
    buttons.append([KeyboardButton(text=t("buttons.back"))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def subscription_keyboard(t: LocalizationFn) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("buttons.check_subscription"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


__all__ = [
    "LocalizationFn",
    "main_menu_keyboard",
    "start_keyboard",
    "cancel_keyboard",
    "wallet_confirmation_keyboard",
    "wallet_choice_keyboard",
    "subscription_keyboard",
]
