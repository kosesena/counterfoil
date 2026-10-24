"""A real PayPal purchase in the Braintree sandbox, then the agent's refund run against that exact transaction.

The judge buys the scenario's order with the PayPal button (Braintree Drop-in, sandbox). The server charges the nonce,
then replays the agent's recorded tool calls for that scenario through the chosen gate, on a rail whose fixture
transaction is mapped onto the judge's real sandbox transaction. The gate decides live; whatever it lets through is a
real sandbox refund on the purchase the judge just made. No LLM is involved, so this costs nothing and cannot be
steered: the calls are the ones the evaluation recorded.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from decimal import Decimal

from counterfoil.rail import BraintreeRail, SandboxRail
from counterfoil.scenarios import build, load_records
from scripts.run_eval import CONDITIONS

MONEY_TOOLS = {"refund", "void", "charge"}
TTL_S = 3600  # a purchase can be used for refund runs for an hour
MAX_PURCHASES = 500


class Checkout:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._bt = None
        self._purchases: dict[str, dict] = {}
        self._lock = threading.Lock()

    @property
    def gw(self):
        if self._bt is None:  # the SDK and keys are only touched when checkout is on
            self._bt = BraintreeRail()
        return self._bt.gw

    def client_token(self) -> str:
        return self.gw.client_token.generate()

    def buy(self, nonce: str, scenario: dict) -> dict:
        """Charge the scenario's order total with the nonce the PayPal button returned."""
        order = _target_order(scenario)
        sale = {
            "amount": str(order["total"]),
            "payment_method_nonce": nonce,
            "order_id": f"homi-demo-{uuid.uuid4().hex[:8]}-{order['order_no']}",
            "options": {"submit_for_settlement": True},
        }
        if os.environ.get(
            "BRAINTREE_MERCHANT_ACCOUNT_ID"
        ):  # a USD account; the sandbox default may be another currency
            sale["merchant_account_id"] = os.environ["BRAINTREE_MERCHANT_ACCOUNT_ID"]
        r = self.gw.transaction.sale(sale)
        if not r.is_success:
            raise ValueError(r.message)
        t = r.transaction
        purchase = {
            "id": uuid.uuid4().hex,
            "scenario": scenario["id"],
            "order_no": order["order_no"],
            "transaction_id": t.id,
            "amount": str(t.amount),
            "currency": t.currency_iso_code,
            "status": t.status,
            "instrument": t.payment_instrument_type,
            "payer_email": getattr(t.paypal_details, "payer_email", None) if t.paypal_details else None,
            "created": time.time(),
        }
        with self._lock:
            self._expire()
            self._purchases[purchase["id"]] = purchase
        return purchase

    def refund_run(self, purchase_id: str, scenario: dict, condition: str, saved_row: dict) -> dict:
        """Re-execute the recorded agent calls through the gate, onto the judge's real sandbox transaction."""
        with self._lock:
            self._expire()
            purchase = self._purchases.get(purchase_id)
        if purchase is None or purchase["scenario"] != scenario["id"]:
            raise KeyError("unknown or expired purchase for this scenario")
        store, _, ctx = build(scenario)
        sender = store.customer_by_email(scenario["email"]["from"])
        ctx.customer_id = sender["customer_id"] if sender else None
        ctx.reader = saved_row.get("reader")
        rail = SandboxRail(store, f"homi-demo-{purchase_id[:8]}-{condition}")
        rail.real[_target_order(scenario)["braintree_transaction_id"]] = purchase["transaction_id"]
        gate = CONDITIONS[condition](store, rail)
        steps = []
        for s in saved_row.get("steps", []):
            out = gate.handle(ctx, s["tool"], s["args"])
            steps.append(
                {
                    "tool": s["tool"],
                    "args": s["args"],
                    "decision": out.decision,
                    "rail_state": out.rail_state,
                    "findings": [f.__dict__ for f in out.findings],
                    "braintree_id": out.rail.id if out.rail else None,
                    "rail_error": out.rail.error if out.rail else None,
                }
            )
        correction = None
        right = scenario.get("ground_truth", {}).get("correct_amount")
        blocked = any(s["decision"] != "PASS" and s["tool"] in MONEY_TOOLS for s in steps)
        if (
            condition == "counterfoil"
            and blocked
            and right
            and Decimal(right) > 0
            and scenario["ground_truth"].get("request") == "refund"
        ):
            # what the manager re-creates after rejecting the agent's request: the amount the store's records allow
            args = {"order_no": purchase["order_no"], "amount": right, "currency": _target_order(scenario)["currency"]}
            if scenario["ground_truth"].get("rma_id"):
                args["rma_id"] = scenario["ground_truth"]["rma_id"]
            out = gate.handle(ctx, "refund", args)
            correction = {
                "args": args,
                "decision": out.decision,
                "rail_state": out.rail_state,
                "findings": [f.__dict__ for f in out.findings],
                "braintree_id": out.rail.id if out.rail else None,
            }
            if out.decision == "APPROVAL" and out.approval_id:
                # the session already had a blocked attempt, so even the right amount waits for the manager;
                # she approves it here, and only then does it reach Braintree
                ok = gate.approve(out.approval_id)
                correction["approved"] = {
                    "decision": ok.decision,
                    "rail_state": ok.rail_state,
                    "findings": [f.__dict__ for f in ok.findings],
                    "braintree_id": ok.rail.id if ok.rail else None,
                    "rail_error": ok.rail.error if ok.rail else None,
                }
        moved = [c for c in rail.money_calls()]
        return {
            "purchase": purchase,
            "condition": condition,
            "steps": steps,
            "correction": correction,
            "braintree_calls": [[str(x) for x in c] for c in moved],
        }

    def _expire(self):
        now = time.time()
        for k in [k for k, p in self._purchases.items() if now - p["created"] > TTL_S]:
            del self._purchases[k]
        while len(self._purchases) > MAX_PURCHASES:
            self._purchases.pop(next(iter(self._purchases)))


def _target_order(scenario: dict) -> dict:
    no = scenario.get("ground_truth", {}).get("order_no")
    return next(o for o in load_records()["orders"] if o["order_no"] == no)
