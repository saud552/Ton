"""FSM states for the selling workflow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SellingStates(StatesGroup):
    waiting_for_stars = State(state="waiting_for_stars")
    waiting_for_payment = State(state="waiting_for_payment")
    waiting_for_wallet_choice = State(state="waiting_for_wallet_choice")
    waiting_for_wallet = State(state="waiting_for_wallet")
    confirming_wallet = State(state="confirming_wallet")


class InvoiceCreationStates(StatesGroup):
    waiting_for_wallet_choice = State(state="invoice_wallet_choice")
    waiting_for_wallet = State(state="invoice_wallet")
    waiting_for_payer = State(state="invoice_payer")
    waiting_for_reason = State(state="invoice_reason")
    waiting_for_stars = State(state="invoice_stars")
    awaiting_confirmation = State(state="invoice_confirmation")


__all__ = ["SellingStates", "InvoiceCreationStates"]
