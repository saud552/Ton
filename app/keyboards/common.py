"""Reusable reply keyboards for the bot."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


class Buttons:
    START_SELLING = "بدء عملية البيع 💫"
    CANCEL_OPERATION = "إلغاء العملية ❌"
    CONFIRM_ADDRESS = "تأكيد العنوان ✅"
    TRANSACTION_HISTORY = "سجل المعاملات 📊"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.START_SELLING)],
            [KeyboardButton(text=Buttons.TRANSACTION_HISTORY)],
        ],
        resize_keyboard=True,
        input_field_placeholder="اختر إجراء من القائمة",
    )


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=Buttons.START_SELLING)]],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=Buttons.CANCEL_OPERATION)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def wallet_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.CONFIRM_ADDRESS)],
            [KeyboardButton(text=Buttons.CANCEL_OPERATION)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


__all__ = [
    "Buttons",
    "main_menu_keyboard",
    "start_keyboard",
    "cancel_keyboard",
    "wallet_confirmation_keyboard",
]
