"""The store-wide refund sweep (counterfoil/reconcile.py) against the in-memory rail."""

import json
from datetime import UTC, datetime
from decimal import Decimal

from counterfoil.gateway import Context, Gateway
from counterfoil.rail import FakeRail
from counterfoil.reconcile import sweep
from counterfoil.scenarios import load_records
from counterfoil.store import Store

SINCE = datetime(2026, 10, 1, tzinfo=UTC)


def setup():
    store = Store(load_records())
    return store, FakeRail.from_store(store)


def test_refunds_the_store_made_or_knows_of_are_not_reported():
    store, rail = setup()
    args = {"order_no": "ST-1042", "rma_id": "RMA-1042", "amount": "30.00", "currency": "USD"}
    reader = {"istek": "refund", "siparis_no": "ST-1042", "tutar": "30.00", "para_birimi": "USD"}
    assert (
        Gateway(store, rail)
        .handle(Context("s", "CUS-01", frozenset({"refund"}), reader=reader), "refund", args)
        .executed
    )
    report = sweep(store, rail, SINCE)
    assert report.clean and report.seen == 2  # ours, and ST-1050's completed refund from the fixtures


def test_a_refund_behind_the_gate_s_back_is_reported_with_its_id():
    store, rail = setup()
    behind = rail.refund("fixture-txn-002", Decimal("15.00"))
    report = sweep(store, rail, SINCE)
    assert report.unknown == [
        {
            "order_no": "ST-1043",
            "rail_total": Decimal("15.00"),
            "store_total": Decimal("0.00"),
            "difference": Decimal("15.00"),
            "refunds_the_store_does_not_list": [behind.id],
        }
    ]


def test_a_store_that_counts_more_than_the_rail_is_not_an_unknown_refund():
    # ST-1051 has a refund of unknown outcome in the ledger; the rail shows none. That is the gate's
    # REFUND_OUTCOME_UNKNOWN to resolve, not money the store did not know went out.
    store, rail = setup()
    assert store.order_refunded_total("ST-1051") == Decimal("50.00")
    assert sweep(store, rail, SINCE).clean


def test_refunds_on_other_transactions_and_standalone_credits_are_listed():
    store, rail = setup()
    rail.refund_log += [
        {"id": "x1", "refunded_transaction_id": "not-a-store-sale", "amount": Decimal("9.00"), "status": "settled"},
        {"id": "c1", "refunded_transaction_id": None, "amount": Decimal("3.00"), "status": "settled"},
        {"id": "f1", "refunded_transaction_id": None, "amount": Decimal("7.00"), "status": "failed"},
    ]
    report = sweep(store, rail, SINCE)
    assert [r["id"] for r in report.foreign] == ["x1"] and [r["id"] for r in report.credits] == ["c1"]
    assert not report.clean and not report.unknown


def test_the_sweep_script_reports_the_refund_made_behind_the_gate():
    from scripts.sweep_refunds import run

    r = run("fake")
    assert r["throughGate"]["decision"] == "PASS/succeeded" and r["behindTheGate"]["ok"]
    assert [u["order_no"] for u in r["unknown"]] == ["ST-1043"]
    assert r["unknown"][0]["refunds_the_store_does_not_list"] == [r["behindTheGate"]["railId"]]
    json.dumps(r)  # what record_rail_checks.py writes for the dashboard
