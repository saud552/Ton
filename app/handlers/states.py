"""FSM states for the selling workflow."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SellingStates(StatesGroup):
    waiting_for_stars = State(state="waiting_for_stars")
    waiting_for_payment = State(state="waiting_for_payment")
    waiting_for_wallet = State(state="waiting_for_wallet")
    confirming_wallet = State(state="confirming_wallet")


__all__ = ["SellingStates"]
