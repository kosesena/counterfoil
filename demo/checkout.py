"""A real PayPal purchase in the Braintree sandbox, then the agent's refund run against that exact transaction.

The judge buys the scenario's order with the PayPal button (Braintree Drop-in, sandbox). The server charges the nonce,
then replays the agent's recorded tool calls for that scenario through the chosen gate, on a rail whose fixture
transaction is mapped onto the judge's real sandbox transaction. The gate decides live; whatever it lets through is a
real sandbox refund on the purchase the judge just made. No LLM is involved, so this costs nothing and cannot be
steered: the calls are the ones the evaluation recorded.

A held call (APPROVAL) waits for the judge, acting as the store's manager: `decide` approves or rejects it through the
gateway's own single-use, time-limited, argument-bound approval. Nothing held reaches Braintree before that.

`rail_rules` shows, on fresh sandbox sales, what Braintree refuses on its own and what it lets through: on a card,
refunds before settlement (91506), above the sale (91521) and after a full refund (91512), with
`testing.settle_transaction` in between; the same calls on mocked PayPal; and a refund on top of an open chargeback
(test card 4023898493988028), next to the gate's decision on it.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from counterfoil.gateway import Context, Gateway
from counterfoil.rail import BraintreeRail, SandboxRail, sale_line_items
from counterfoil.scenarios import build, load_records
from counterfoil.store import Store
from scripts.run_eval import CONDITIONS

MONEY_TOOLS = {"refund", "void", "charge"}
TTL_S = 3600  # a purchase can be used for refund runs for an hour
MAX_PURCHASES = 500
MAX_RUNS = 500
DISPUTE_CARD = "4023898493988028"  # Braintree's test card that opens a chargeback on the sale
DISPUTE_ORDER = "ST-1056"  # a card order of the fixture store, RMA-1056 approves 40.00


class Checkout:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._bt = None
        self._purchases: dict[str, dict] = {}
        self._runs: dict[str, dict] = {}  # run id -> the gate, its rail and the response, while calls are held
        self._held: dict[str, str] = {}  # approval id -> run id
        self._stories: dict[str, dict] = {}  # story session id (from the dashboard's QR) -> {created, purchase id}
        self._lock = threading.Lock()

    @property
    def gw(self):
        if self._bt is None:  # the SDK and keys are only touched when checkout is on
            self._bt = BraintreeRail()
        return self._bt.gw

    def client_token(self) -> str:
        return self.gw.client_token.generate()

    def buy(self, nonce: str, scenario: dict, extras: tuple[tuple[str, str], ...] = ()) -> dict:
        """Charge the scenario's order total with the nonce the PayPal button returned. `extras` are other lines on
        the same receipt (the story's rug and plant): they add to the sale, never to the order the refund is checked
        against."""
        order = _target_order(scenario)
        total = Decimal(str(order["total"])) + sum((Decimal(p) for _, p in extras), Decimal(0))
        sale = {
            "amount": str(total),
            "payment_method_nonce": nonce,
            "order_id": f"homi-demo-{uuid.uuid4().hex[:8]}-{order['order_no']}",
            "line_items": sale_line_items(build(scenario)[0], order)
            + [
                {
                    "kind": "debit",
                    "name": name[:35],
                    "product_code": name.upper().replace(" ", "-")[:12],
                    "quantity": "1",
                    "unit_amount": price,
                    "total_amount": price,
                }
                for name, price in extras
            ],
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
            "lines": [{"item": "order " + order["order_no"], "amount": str(order["total"])}]
            + [{"item": i, "amount": p} for i, p in extras],
            "created": time.time(),
        }
        with self._lock:
            self._expire()
            self._purchases[purchase["id"]] = purchase
        return purchase

    def story_pay(self, sid: str, nonce: str, scenario: dict, extras: tuple[tuple[str, str], ...]) -> dict:
        """The phone that scanned the dashboard's QR pays here; the dashboard then sees the purchase by `sid`."""
        with self._lock:
            self._expire()
            known = self._stories.get(sid)
            if known and known.get("purchase"):
                return self._purchases[known["purchase"]]  # paid once; a second tap shows the same sale
            if not known and len(self._stories) >= MAX_PURCHASES:
                raise OverflowError("too many open store sessions")
            self._stories[sid] = {"created": time.time(), "purchase": None}
        purchase = self.buy(nonce, scenario, extras)
        with self._lock:
            self._stories[sid]["purchase"] = purchase["id"]
        return purchase

    def story_status(self, sid: str) -> dict:
        with self._lock:
            self._expire()
            story = self._stories.get(sid)
            p = self._purchases.get(story["purchase"]) if story and story.get("purchase") else None
        if p is None:
            return {"status": "waiting"}
        keep = ("id", "transaction_id", "amount", "currency", "status", "instrument", "lines")
        return {"status": "paid", "purchase": {k: p[k] for k in keep if k in p}}

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
                {"tool": s["tool"], "args": s["args"], **_outcome(out), **_review(store, s["tool"], s["args"], out)}
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
            # the session already had a blocked attempt, so even the right amount waits for the manager
            correction = {"tool": "refund", "args": args, **_outcome(out), **_review(store, "refund", args, out)}
        result = {
            "run_id": uuid.uuid4().hex,
            "purchase": purchase,
            "condition": condition,
            "steps": steps,
            "correction": correction,
            "braintree_calls": _calls(rail),
        }
        held = [c["approval_id"] for c in [*steps, correction] if c and c.get("approval_id")]
        if held:
            with self._lock:
                self._expire()
                self._runs[result["run_id"]] = {
                    "purchase_id": purchase_id,
                    "gate": gate,
                    "rail": rail,
                    "result": result,
                    "lock": threading.Lock(),
                    "created": time.time(),
                }
                self._held.update(dict.fromkeys(held, result["run_id"]))
        return result

    def decide(self, purchase_id: str, approval_id: str, approve: bool) -> dict:
        """The manager's answer to one held call. Only an approval sends it on, and only through `Gateway.approve`,
        which re-runs the checks and refuses an expired, reused or altered approval."""
        with self._lock:
            self._expire()
            run = self._runs.get(self._held.get(approval_id, ""))
            if run is None or run["purchase_id"] != purchase_id:
                raise KeyError("no such held call for this purchase (or it was already decided)")
            del self._held[approval_id]  # single use, even if two answers race
        with run["lock"]:
            result = run["result"]
            item = next(
                c for c in [*result["steps"], result["correction"]] if c and c.get("approval_id") == approval_id
            )
            if approve:
                item["approved"] = _outcome(run["gate"].approve(approval_id))
            else:
                run["gate"].reject(approval_id)
                item["rejected"] = True
            item["approval_id"] = None
            result["braintree_calls"] = _calls(run["rail"])
            return result

    def rail_rules(self) -> dict:
        """Fresh sandbox sales, straight to Braintree (no gate): what does the rail itself refuse?"""
        return {"card": self._card_rules(), "paypal": self._paypal_rules(), "dispute": self._dispute_rules()}

    def _account(self) -> dict:
        acct = os.environ.get("BRAINTREE_MERCHANT_ACCOUNT_ID")
        return {"merchant_account_id": acct} if acct else {}

    def _step(self, label: str, r) -> dict:
        if r.is_success:
            t = r.transaction
            return {"label": label, "ok": True, "id": t.id, "status": t.status, "amount": str(t.amount)}
        errors = "; ".join(f"{e.code} {e.message}" for e in r.errors.deep_errors) or r.message
        return {"label": label, "ok": False, "error": errors}

    def _sale(self, label: str, params: dict) -> tuple[dict, str | None]:
        cents = Decimal(uuid.uuid4().int % 99 + 1) / 100  # identical sales within 30 s are rejected as duplicates
        amount = Decimal(params.pop("base", "50.00")) + cents
        step = self._step(
            f"{label} {amount}",
            self.gw.transaction.sale(
                {"amount": str(amount), **params, "options": {"submit_for_settlement": True}, **self._account()}
            ),
        )
        return step, step.get("id")

    def _card_rules(self) -> list[dict]:
        sale, tid = self._sale("card sale", {"payment_method_nonce": "fake-valid-nonce"})
        if tid is None:
            return [sale]
        amount = Decimal(sale["amount"])
        return [
            sale,
            self._step("refund 10.00 before settlement", self.gw.transaction.refund(tid, "10.00")),
            self._step("testing.settle_transaction", self.gw.testing.settle_transaction(tid)),
            self._step(f"refund {amount + 10} (more than the sale)", self.gw.transaction.refund(tid, str(amount + 10))),
            self._step(f"refund {amount} (all of it)", self.gw.transaction.refund(tid, str(amount))),
            self._step("refund 1.00 more", self.gw.transaction.refund(tid, "1.00")),
        ]

    def _paypal_rules(self) -> list[dict]:
        sale, tid = self._sale("mocked PayPal sale", {"payment_method_nonce": "fake-paypal-one-time-nonce"})
        if tid is None:
            return [sale]
        amount = Decimal(sale["amount"])
        return [
            sale,
            self._step("refund 10.00 before settlement", self.gw.transaction.refund(tid, "10.00")),
            self._step(
                f"refund {amount} (with the 10.00, more than the sale)", self.gw.transaction.refund(tid, str(amount))
            ),
            self._step("refund 1.00 more", self.gw.transaction.refund(tid, "1.00")),
        ]

    def _dispute_rules(self) -> list[dict]:
        records = load_records()
        order = next(o for o in records["orders"] if o["order_no"] == DISPUTE_ORDER)
        sale, tid = self._sale(
            "sale on the dispute test card",
            {"base": order["total"], "credit_card": {"number": DISPUTE_CARD, "expiration_date": "12/2030"}},
        )
        if tid is None:
            return [sale]
        disputes = []
        for _ in range(8):  # the sandbox opens the chargeback within seconds
            disputes = self.gw.transaction.find(tid).disputes or []
            if disputes:
                break
            time.sleep(1.5)
        steps = [
            sale,
            {
                "label": "disputes on the sale",
                "ok": bool(disputes),
                "disputes": [
                    {"id": d.id, "status": d.status, "kind": d.kind, "amount": str(d.amount_disputed)} for d in disputes
                ],
                **({} if disputes else {"error": "no dispute showed up yet"}),
            },
            self._step("testing.settle_transaction", self.gw.testing.settle_transaction(tid)),
        ]
        # The gate's check of the agent's refund for this order's return record, with the order mapped onto this sale.
        store = Store(records)
        rail = SandboxRail(store, f"rail-rules-{tid}")
        rail.real[order["braintree_transaction_id"]] = tid
        rma = order["returns"][0]
        args = {
            "order_no": DISPUTE_ORDER,
            "rma_id": rma["rma_id"],
            "amount": rma["approved_refund_amount"],
            "currency": "USD",
        }
        reader = {"istek": "refund", "siparis_no": DISPUTE_ORDER, "tutar": args["amount"], "para_birimi": "USD"}
        created = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
        ctx = Context(
            "rail-rules", order["customer_id"], frozenset({"refund"}), reader=reader, as_of=created + timedelta(days=5)
        )
        findings = Gateway(store, rail).check(ctx, "refund", args)
        blocked = [f for f in findings if f.severity == "BLOCK"]
        steps.append(
            {
                "label": f"Counterfoil: refund {args['amount']} for {rma['rma_id']}",
                "ok": not blocked,
                "gate": "BLOCK" if blocked else ("APPROVAL" if findings else "PASS"),
                "findings": [f.__dict__ for f in findings],
            }
        )
        steps.append(
            self._step(f"Braintree alone: refund {args['amount']}", self.gw.transaction.refund(tid, args["amount"]))
        )
        return steps

    def _expire(self):
        now = time.time()
        for k in [k for k, p in self._purchases.items() if now - p["created"] > TTL_S]:
            del self._purchases[k]
        while len(self._purchases) > MAX_PURCHASES:
            self._purchases.pop(next(iter(self._purchases)))
        for k in [
            k for k, r in self._runs.items() if now - r["created"] > TTL_S or r["purchase_id"] not in self._purchases
        ]:
            del self._runs[k]
        while len(self._runs) > MAX_RUNS:
            self._runs.pop(next(iter(self._runs)))
        for k in [k for k, st in self._stories.items() if now - st["created"] > TTL_S]:
            del self._stories[k]
        for a in [a for a, r in self._held.items() if r not in self._runs]:
            del self._held[a]


def _target_order(scenario: dict) -> dict:
    no = scenario.get("ground_truth", {}).get("order_no")
    return next(o for o in load_records()["orders"] if o["order_no"] == no)


def _outcome(out) -> dict:
    return {
        "decision": out.decision,
        "rail_state": out.rail_state,
        "findings": [f.__dict__ for f in out.findings],
        "braintree_id": out.rail.id if out.rail else None,
        "rail_error": out.rail.error if out.rail else None,
    }


def _review(store, tool: str, args: dict, out) -> dict:
    """What the manager sees next to a held call: the store record the gate checked it against, as it is now."""
    if out.decision != "APPROVAL" or not out.approval_id:
        return {}
    record: dict = {}
    order = store.orders.get(str(args.get("order_no", "")))
    if tool == "refund" and order is not None:
        rma_id = args.get("rma_id") if isinstance(args.get("rma_id"), str) else None
        ent = store.entitlement(order["order_no"], rma_id)
        record = {
            "order_no": order["order_no"],
            "order_total": str(order["total"]),
            "rma_id": rma_id if store.rma(order["order_no"], rma_id) else None,
            "approved": str(ent.approved),
            "refunded": str(ent.spent),
            "reserved": str(ent.reserved),
            "left": str(max(ent.remaining, Decimal("0.00"))),
        }
    elif tool == "charge":
        items = [i for i in args.get("items") or [] if isinstance(i, dict)]
        record = {
            "catalog": [
                {"sku": str(i.get("sku")), "unit_price": store.catalog[i["sku"]]["unit_price"]}
                for i in items
                if i.get("sku") in store.catalog
            ],
            "quantity_on_record": None,  # no store record says how many; only the e-mail does
        }
    return {"approval_id": out.approval_id, "record": record}


def _calls(rail) -> list[list[str]]:
    return [[str(x) for x in c] for c in rail.money_calls()]
