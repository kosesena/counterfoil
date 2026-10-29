"""Braintree webhooks: the rail tells the store what happened between agent calls.

The gate reads disputes and refunds from the rail when an agent asks for a refund. A webhook moves that earlier: when
Braintree opens a chargeback, the store marks the transaction disputed at once, and every later refund on it is
blocked (TRANSACTION_DISPUTED) without waiting for the next refund to look. A refund already held for a manager is
refused on approval too, because approval re-runs the checks.

`receive` takes the two form fields Braintree posts (bt_signature, bt_payload). The signature is checked by the
official SDK (`webhook_notification.parse`, HMAC-SHA1 with the merchant's private key); anything that does not verify
raises `Unverified` and changes nothing. Every verified notification gets one audit row in the store, keyed by the
sha256 of its payload, so the same notification delivered twice is recorded once and acted on once. Dispute statuses
are applied by notification time, so a late, older notification cannot reopen or close a dispute.

What each kind does (Braintree's list: braintree.WebhookNotification.Kind, SDK 4.48):

- dispute_opened, dispute_under_review, dispute_disputed, dispute_won, dispute_lost, dispute_accepted,
  dispute_auto_accepted, dispute_expired → the dispute's status is stored against its transaction. Only won lifts the
  lock (the gate's existing rule); lost, accepted and expired keep it, since the chargeback has paid the customer.
- refund_failed → a refund the store counted as gone failed on the rail: the ledger row is marked failed, which is
  what reconciliation does. A failed refund the store never made is flagged.
- transaction_settled, transaction_settlement_declined, transaction_disbursed, disbursement → the store-wide refund
  sweep (counterfoil/reconcile.py) runs, and refunds the store does not know about are flagged in the audit row.
- check (the Control Panel's "Check URL" button) → recorded, nothing else.
- anything else (subscriptions, local payments, OAuth, partner merchants) → recorded as ignored.

Braintree sends no webhook when a refund or credit is created, so a refund made in the Control Panel is found by the
sweep on the next settlement or disbursement notification, or by the gate's per-transaction check before the next
refund on that order. transaction_settled and transaction_settlement_declined are only sent for some payment methods
(ACH, local payments), not for cards or PayPal; disbursement is daily. On 29 Oct the sandbox Control Panel offered
none of the four to this merchant (only the dispute kinds and refund_failed), so the sweep mostly runs on its own.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .rail import Rail
from .reconcile import sweep
from .store import Store

DISPUTE_KINDS = frozenset(
    {
        "dispute_opened",
        "dispute_under_review",
        "dispute_disputed",
        "dispute_won",
        "dispute_lost",
        "dispute_accepted",
        "dispute_auto_accepted",
        "dispute_expired",
    }
)
SWEEP_KINDS = frozenset(
    {"transaction_settled", "transaction_settlement_declined", "transaction_disbursed", "disbursement"}
)
SWEEP_WINDOW = timedelta(days=30)  # how far back the sweep a notification triggers looks for refunds


class Unverified(Exception):
    """The notification's signature or payload did not verify; nothing was recorded."""


@dataclass(frozen=True)
class Received:
    event_id: str
    kind: str
    action: str  # what the store did: dispute_locked, dispute_unlocked, dispute_unchanged, refund_failed, swept, ...
    detail: dict
    duplicate: bool = False  # this exact notification was received before; nothing changed


def _iso(t: datetime | None) -> str:
    if t is None:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if t.tzinfo is None:  # the SDK parses Braintree's UTC timestamps as naive datetimes
        t = t.replace(tzinfo=UTC)
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_id(payload: str | bytes) -> str:
    raw = payload.encode("ascii") if isinstance(payload, str) else payload
    return hashlib.sha256(raw.strip()).hexdigest()


class Webhooks:
    """`gateway` is a configured braintree.BraintreeGateway (its keys verify the signature). `rail` is what the sweep
    asks for refunds; without one, settlement notifications are recorded but not swept."""

    def __init__(self, store: Store, gateway, rail: Rail | None = None, clock: Callable[[], datetime] | None = None):
        self.store, self.gw, self.rail = store, gateway, rail
        self.clock = clock or (lambda: datetime.now(UTC))

    def receive(self, signature: str | None, payload: str | None) -> Received:
        import braintree

        try:
            note = self.gw.webhook_notification.parse(signature, payload)
        except (braintree.exceptions.InvalidSignatureError, ValueError, KeyError, TypeError) as exc:
            raise Unverified(type(exc).__name__) from None
        eid = event_id(payload or "")
        with self.store.transaction():  # check, act and record as one step: two deliveries cannot both act
            old = self.store.event(eid)
            if old is not None:
                return Received(eid, old["kind"], old["action"], old["detail"], duplicate=True)
            kind = note.kind
            sent_at = _iso(note.timestamp)
            subject, action, detail = self._act(note, kind, sent_at)
            self.store.record_event(eid, kind, subject, sent_at, _iso(self.clock()), action, detail)
        return Received(eid, kind, action, json.loads(json.dumps(detail, default=str)))

    # -- per kind --------------------------------------------------------------------------------
    def _act(self, note, kind: str, sent_at: str) -> tuple[str | None, str, dict]:
        if kind in DISPUTE_KINDS:
            return self._dispute(note.dispute, kind, sent_at)
        if kind == "refund_failed":
            return self._refund_failed(note.transaction)
        if kind in SWEEP_KINDS:
            return self._sweep(note, kind)
        if kind == "check":
            return None, "checked", {}
        return None, "ignored", {"why": f"Counterfoil does not act on {kind}"}

    def _dispute(self, d, kind: str, sent_at: str) -> tuple[str, str, dict]:
        txn = d.transaction.id
        before = {x["id"]: x["status"] for x in self.store.disputes_on(txn)}.get(d.id)
        changed = self.store.record_dispute(
            d.id, txn, d.kind, d.status, str(d.amount_disputed), sent_at, f"webhook {kind}"
        )
        locked = any(x["status"] != "won" for x in self.store.disputes_on(txn))
        detail = {
            "dispute_id": d.id,
            "transaction_id": txn,
            "dispute_kind": d.kind,
            "status": d.status,
            "previous_status": before,
            "amount": str(d.amount_disputed),
            "reason": d.reason,
            "refunds_on_transaction": "blocked" if locked else "allowed",
        }
        action = "dispute_unchanged" if not changed else "dispute_locked" if locked else "dispute_unlocked"
        return txn, action, detail

    def _refund_failed(self, t) -> tuple[str, str, dict]:
        known = self.store.sql("SELECT order_no, status FROM refunds WHERE refund_id=?", (t.id,))
        detail = {
            "refund_id": t.id,
            "rail_status": t.status,
            "refunded_transaction_id": getattr(t, "refunded_transaction_id", None),
        }
        if not known:
            return t.id, "flagged", {**detail, "why": "a refund the store's ledger does not list failed on the rail"}
        self.store.set_refund_status(t.id, "failed")
        return t.id, "refund_failed", {**detail, "order_no": known[0][0], "ledger_status_before": known[0][1]}

    def _sweep(self, note, kind: str) -> tuple[str | None, str, dict]:
        subject = getattr(getattr(note, "transaction", None), "id", None) or getattr(
            getattr(note, "disbursement", None), "id", None
        )
        if self.rail is None or not hasattr(self.rail, "refunds"):
            return subject, "recorded", {"why": "no rail to sweep on this server"}
        since = self.clock() - SWEEP_WINDOW
        report = sweep(self.store, self.rail, since)
        detail = {
            "since": _iso(since),
            "refunds_seen": report.seen,
            "unknown": report.unknown,
            "foreign": [r["id"] for r in report.foreign],
            "credits": [r["id"] for r in report.credits],
        }
        return subject, "swept" if report.clean else "flagged", detail
