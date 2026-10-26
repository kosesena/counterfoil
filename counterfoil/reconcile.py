"""The store-wide refund sweep: every refund and credit the rail sent out, against the store's refund ledger.

The gate already compares the rail with the store per transaction before each refund (UNRECONCILED_RAIL_REFUNDS).
That only looks at an order when someone asks to refund it. The sweep asks the rail once for everything that went out
since a moment and reports what the store does not know about:

- unknown refunds: an order whose transaction the rail refunded more than the store's ledger says (a refund made in
  the Braintree Control Panel, by another tool, or one the store lost);
- refunds on transactions that are no order of this store;
- standalone credits: money sent out with no sale behind it (Braintree transaction.credit).

Only refunds created since `since` are seen, so pick a moment before the oldest order you care about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from .rail import Rail
from .store import Store


@dataclass
class Sweep:
    since: datetime
    seen: int = 0  # refunds and credits the rail listed
    unknown: list[dict] = field(default_factory=list)  # per order: rail total above the store's
    foreign: list[dict] = field(default_factory=list)  # refunds on transactions that are no order of this store
    credits: list[dict] = field(default_factory=list)  # money out with no sale behind it

    @property
    def clean(self) -> bool:
        return not (self.unknown or self.foreign or self.credits)


def sweep(store: Store, rail: Rail, since: datetime) -> Sweep:
    orders = {o["braintree_transaction_id"]: o for o in store.orders.values()}
    out = Sweep(since)
    per_order: dict[str, list[dict]] = {}
    for r in rail.refunds(since):
        out.seen += 1
        parent = r["refunded_transaction_id"]
        if parent is None:
            out.credits.append(r)
        elif parent in orders:
            per_order.setdefault(orders[parent]["order_no"], []).append(r)
        else:
            out.foreign.append(r)
    for order_no, refunds in sorted(per_order.items()):
        rail_total = sum((r["amount"] for r in refunds), Decimal("0.00"))
        local = store.order_refunded_total(order_no)
        if rail_total > local:
            known = {rid for (rid,) in store.sql("SELECT refund_id FROM refunds WHERE order_no=?", (order_no,))}
            out.unknown.append(
                {
                    "order_no": order_no,
                    "rail_total": rail_total,
                    "store_total": local,
                    "difference": rail_total - local,
                    "refunds_the_store_does_not_list": [r["id"] for r in refunds if r["id"] not in known],
                }
            )
    return out
