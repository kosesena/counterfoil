"""Braintree webhooks (counterfoil/webhooks.py), with no network: the notifications are the SDK's own
`webhook_testing.sample_notification`, signed with a sandbox-style configuration and verified by
`webhook_notification.parse` exactly as a real delivery would be."""

from datetime import UTC, datetime
from decimal import Decimal

import braintree
import braintree.webhook_testing_gateway as testing_gateway
import pytest

from counterfoil.gateway import BLOCK, PASS, Context, Gateway
from counterfoil.rail import FakeRail
from counterfoil.scenarios import load_records
from counterfoil.store import Store
from counterfoil.webhooks import DISPUTE_KINDS, SWEEP_KINDS, Unverified, Webhooks

GW = braintree.BraintreeGateway(
    braintree.Configuration(braintree.Environment.Sandbox, "test-merchant", "test-public", "test-private")
)
OTHER = braintree.BraintreeGateway(  # same public key, another private key: a forger who knows the public key
    braintree.Configuration(braintree.Environment.Sandbox, "test-merchant", "test-public", "not-the-key")
)
AS_OF = datetime(2026, 10, 23, 12, tzinfo=UTC)
TXN = "fixture-txn-001"  # ST-1042
REFUND = {"order_no": "ST-1042", "rma_id": "RMA-1042", "amount": "30.00", "currency": "USD"}
READER = {
    "istek": "refund",
    "siparis_no": "ST-1042",
    "iade_kaydi_no": "RMA-1042",
    "tutar": "30.00",
    "para_birimi": "USD",
}


def setup():
    store = Store(load_records())
    rail = FakeRail.from_store(store)  # the fake rail lists no disputes: any lock below comes from the webhook alone
    return store, rail, Webhooks(store, GW, rail), Gateway(store, rail)


class _SentAt(datetime):
    at: datetime | None = None

    @classmethod
    def utcnow(cls):
        return cls.at or datetime.now(UTC).replace(tzinfo=None)


testing_gateway.datetime = _SentAt  # the SDK stamps samples with utcnow(); tests choose when a notification was sent


def sample(kind, id=TXN, gw=GW, at=None):
    _SentAt.at = at
    try:
        n = gw.webhook_testing.sample_notification(kind, id)
    finally:
        _SentAt.at = None
    return n["bt_signature"], n["bt_payload"]


def session():
    return Context("s1", "CUS-01", frozenset({"refund"}), reader=dict(READER), as_of=AS_OF)


def refund(gate):
    return gate.handle(session(), "refund", REFUND)


# -- signature -------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "forge",
    [
        lambda s, p: (None, p),
        lambda s, p: (s, None),
        lambda s, p: ("", p),
        lambda s, p: ("test-public|" + "0" * 40, p),
        lambda s, p: (s, p.decode()[:30] + ("A" if p.decode()[30] != "A" else "B") + p.decode()[31:]),
        lambda s, p: (s, "<notification/>"),
        lambda s, p: sample("dispute_opened", gw=OTHER),
    ],
    ids=["no signature", "no payload", "blank signature", "wrong hmac", "payload changed", "raw xml", "other key"],
)
def test_anything_unverified_is_refused_and_changes_nothing(forge):
    store, _, hooks, gate = setup()
    with pytest.raises(Unverified):
        hooks.receive(*forge(*sample("dispute_opened")))
    assert store.events() == [] and store.disputes_on(TXN) == []
    assert refund(gate).decision == PASS


# -- disputes --------------------------------------------------------------------------------------
def test_dispute_webhook_blocks_the_next_refund_on_that_transaction():
    store, rail, hooks, gate = setup()
    assert refund(gate).decision == PASS  # before: the store and the rail know of no dispute
    got = hooks.receive(*sample("dispute_opened"))
    assert got.action == "dispute_locked" and got.detail["refunds_on_transaction"] == "blocked"
    out = refund(gate)
    assert out.decision == BLOCK and not out.reached_rail
    found = next(f for f in out.findings if f.code == "TRANSACTION_DISPUTED")
    assert "chargeback" in found.detail and "from webhook dispute_opened" in found.detail
    assert rail.disputes(TXN) == []  # the rail was asked and listed nothing; the store's record held


def test_only_won_lifts_the_lock():
    store, _, hooks, gate = setup()
    hooks.receive(*sample("dispute_opened", at=datetime(2026, 10, 27, 9)))
    won = hooks.receive(*sample("dispute_won", at=datetime(2026, 10, 27, 10)))
    assert won.action == "dispute_unlocked" and won.detail["previous_status"] == "open"
    assert refund(gate).decision == PASS


@pytest.mark.parametrize("kind", sorted(DISPUTE_KINDS - {"dispute_won"}))
def test_every_other_dispute_state_keeps_refunds_blocked(kind):
    store, _, hooks, gate = setup()
    got = hooks.receive(*sample(kind))
    assert got.kind == kind and got.action == "dispute_locked"
    assert store.disputes_on(TXN)[0]["status"] == got.detail["status"] != "won"
    assert refund(gate).decision == BLOCK


def test_a_lost_dispute_after_a_win_locks_again_and_an_older_notification_changes_nothing():
    store, _, hooks, gate = setup()
    hooks.receive(*sample("dispute_won", at=datetime(2026, 10, 27, 9)))
    assert refund(gate).decision == PASS
    hooks.receive(*sample("dispute_lost", at=datetime(2026, 10, 28, 9)))
    assert refund(gate).decision == BLOCK
    late = hooks.receive(*sample("dispute_opened", at=datetime(2026, 10, 26, 9)))  # retried late, sent first
    assert late.action == "dispute_unchanged" and store.disputes_on(TXN)[0]["status"] == "lost"
    assert len(store.events()) == 3  # still audited


def test_a_dispute_on_a_held_refund_refuses_the_approval():
    store, rail, hooks, gate = setup()
    ctx = session()
    held = gate.handle(ctx, "refund", dict(REFUND, amount="31.00"))  # above the RMA's 30.00: waits for the manager
    assert held.decision == "APPROVAL"
    hooks.receive(*sample("dispute_opened"))
    out = gate.approve(held.approval_id)
    assert out.decision == BLOCK and "TRANSACTION_DISPUTED" in {f.code for f in out.findings}
    assert rail.money_calls() == []


def test_the_same_notification_twice_changes_nothing():
    store, _, hooks, _ = setup()
    sig, payload = sample("dispute_opened")
    first = hooks.receive(sig, payload)
    second = hooks.receive(sig, payload)
    assert not first.duplicate and second.duplicate
    assert (second.event_id, second.action, second.detail) == (first.event_id, first.action, first.detail)
    assert len(store.events()) == 1 and len(store.disputes_on(TXN)) == 1


def test_a_new_notification_of_the_same_dispute_state_is_audited_but_changes_no_lock():
    store, _, hooks, _ = setup()
    hooks.receive(*sample("dispute_opened", at=datetime(2026, 10, 27, 9)))
    again = hooks.receive(*sample("dispute_opened", at=datetime(2026, 10, 27, 10)))
    assert not again.duplicate and again.action == "dispute_locked" and again.detail["previous_status"] == "open"
    assert [d["status"] for d in store.disputes_on(TXN)] == ["open"] and len(store.events()) == 2


def test_audit_row_per_event_newest_first():
    store, _, hooks, _ = setup()
    hooks.receive(*sample("check", at=datetime(2026, 10, 27, 9)))
    hooks.receive(*sample("dispute_opened", at=datetime(2026, 10, 27, 10)))
    events = store.events()
    assert [e["kind"] for e in events] == ["dispute_opened", "check"]
    assert events[0]["action"] == "dispute_locked" and events[0]["subject_id"] == TXN
    assert events[0]["detail"]["dispute_kind"] == "chargeback" and events[1]["action"] == "checked"


# -- refunds and settlement ------------------------------------------------------------------------
def test_refund_failed_marks_the_ledger_row_failed():
    store, rail, hooks, gate = setup()
    out = refund(gate)
    assert out.executed
    got = hooks.receive(*sample("refund_failed", out.rail.id))
    assert got.action == "refund_failed" and got.detail["ledger_status_before"] == "accepted"
    assert store.sql("SELECT status FROM refunds WHERE refund_id=?", (out.rail.id,)) == [("failed",)]


def test_refund_failed_the_store_never_made_is_flagged():
    store, _, hooks, _ = setup()
    got = hooks.receive(*sample("refund_failed", "refund-nobody-made"))
    assert got.action == "flagged" and "does not list" in got.detail["why"]


@pytest.mark.parametrize("kind", sorted(SWEEP_KINDS))
def test_settlement_notifications_sweep_and_flag_refunds_made_behind_the_gate(kind):
    store, rail, hooks, _ = setup()
    assert hooks.receive(*sample(kind, "settle-1")).action == "swept"
    behind = rail.refund("fixture-txn-002", Decimal("15.00"))  # e.g. in the Control Panel; no webhook for that
    got = hooks.receive(*sample(kind, "settle-2"))  # another notification: the same one twice is not acted on twice
    assert got.action == "flagged"
    assert got.detail["unknown"] == [
        {
            "order_no": "ST-1043",
            "rail_total": "15.00",
            "store_total": "0.00",
            "difference": "15.00",
            "refunds_the_store_does_not_list": [behind.id],
        }
    ]


def test_without_a_rail_settlement_is_recorded_not_swept():
    store = Store(load_records())
    got = Webhooks(store, GW).receive(*sample("transaction_settled"))
    assert got.action == "recorded" and store.events()[0]["kind"] == "transaction_settled"


def test_kinds_counterfoil_does_not_act_on_are_recorded_as_ignored():
    store, _, hooks, gate = setup()
    got = hooks.receive(*sample("subscription_canceled"))
    assert got.action == "ignored" and len(store.events()) == 1
    assert refund(gate).decision == PASS
