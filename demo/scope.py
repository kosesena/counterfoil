"""Keeps every demo run inside the fixture store.

The gates decide what the *agent* may do; this decides what the *demo* may do, whatever the gate. A pasted email
under "no gate" can make the agent name any transaction id or payment token it likes, and NoGate forwards it as
is. With the Braintree sandbox behind it that would create or refund real sandbox transactions outside the story,
so the rail is wrapped: only the store's own transaction ids and vaulted tokens get through, anything else fails
like an unknown transaction would. Refused calls never reach the rail, so they are not in `money_calls()`.
"""

from __future__ import annotations

from counterfoil.rail import RailResult

OUT_OF_SCOPE = "OUT_OF_SCOPE not part of the demo store"


class ScopedRail:
    def __init__(self, inner, store, name: str):
        self.inner, self.name = inner, name
        self.txns = {o["braintree_transaction_id"] for o in store.orders.values()}
        self.tokens = {m["token"] for c in store.customers.values() for m in c.get("vaulted_payment_methods", [])}
        self.refused: list[tuple] = []

    def _refuse(self, *call) -> RailResult:
        self.refused.append(call)
        return RailResult(False, error=f"91504 {OUT_OF_SCOPE}: {call[1]!r}")

    def refund(self, transaction_id, amount):
        if transaction_id not in self.txns:
            return self._refuse("refund", transaction_id, amount)
        return self.inner.refund(transaction_id, amount)

    def void(self, transaction_id):
        if transaction_id not in self.txns:
            return self._refuse("void", transaction_id)
        return self.inner.void(transaction_id)

    def charge(self, payment_method_token, amount, order_id):
        if payment_method_token not in self.tokens:
            return self._refuse("charge", payment_method_token, amount)
        return self.inner.charge(payment_method_token, amount, order_id)

    def refunded_total(self, transaction_id):
        return self.inner.refunded_total(transaction_id) if transaction_id in self.txns else None

    def find(self, transaction_id):
        return self.inner.find(transaction_id) if transaction_id in self.txns else None

    def money_calls(self) -> list[tuple]:
        return self.inner.money_calls()
