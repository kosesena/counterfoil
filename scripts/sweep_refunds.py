"""Show the store-wide refund sweep (counterfoil/reconcile.py) on one run.

A refund goes through the gate the normal way (ST-1042, its RMA's 30.00). Then a refund is made straight on the rail,
behind the gate's back, on an order nobody asked to refund (ST-1043, 15.00): what a refund from the Braintree Control
Panel or another tool looks like to the store. The sweep asks the rail once for everything that went out and reports
the second refund; the gate-made one is in the store's ledger and is not reported.

    python scripts/sweep_refunds.py                   # in-memory rail, no keys
    python scripts/sweep_refunds.py --rail braintree  # the Braintree sandbox (BRAINTREE_* in .env)
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from counterfoil.gateway import Context, Gateway  # noqa: E402
from counterfoil.rail import FakeRail, SandboxRail  # noqa: E402
from counterfoil.reconcile import sweep  # noqa: E402
from counterfoil.scenarios import load_records  # noqa: E402
from counterfoil.store import Store  # noqa: E402


def run(rail_kind: str = "fake") -> dict:
    """One gate refund, one refund behind the gate's back, then the sweep. Returns what happened, JSON-ready."""
    store = Store(load_records())
    since = datetime.now(UTC) - timedelta(minutes=1)
    tag = f"sweep-{uuid.uuid4().hex[:8]}"
    rail = SandboxRail(store, tag) if rail_kind == "braintree" else FakeRail.from_store(store)
    gate = Gateway(store, rail)

    args = {"order_no": "ST-1042", "rma_id": "RMA-1042", "amount": "30.00", "currency": "USD"}
    reader = {"istek": "refund", "siparis_no": "ST-1042", "tutar": "30.00", "para_birimi": "USD"}
    out = gate.handle(Context(tag, "CUS-01", frozenset({"refund"}), reader=reader), "refund", args)
    behind = rail.refund("fixture-txn-002", Decimal("15.00"))  # ST-1043; the store's ledger never hears of it
    report = sweep(store, rail, since)
    money = lambda d: {k: str(v) if isinstance(v, Decimal) else v for k, v in d.items()}  # noqa: E731
    return {
        "rail": rail_kind,
        "since": since.isoformat(timespec="seconds"),
        "throughGate": {
            "orderNo": "ST-1042",
            "amount": "30.00",
            "decision": out.summary(),
            "railId": out.rail and out.rail.id,
        },
        "behindTheGate": {
            "orderNo": "ST-1043",
            "amount": "15.00",
            "ok": behind.ok,
            "railId": behind.id,
            "error": behind.error,
        },
        "seen": report.seen,
        "unknown": [money(u) for u in report.unknown],
        "foreign": [money(r) for r in report.foreign],
        "credits": [money(r) for r in report.credits],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rail", choices=["fake", "braintree"], default="fake")
    r = run(ap.parse_args().rail)
    g, b = r["throughGate"], r["behindTheGate"]
    print(f"through the gate:  refund 30.00 on ST-1042 → {g['decision']} (rail id {g['railId']})")
    print(f"behind its back:   refund 15.00 on ST-1043 → {'ok' if b['ok'] else b['error']} (rail id {b['railId']})")
    print(f"\nsweep since {r['since']}: {r['seen']} refund(s)/credit(s) on the rail")
    for u in r["unknown"]:
        print(
            f"  UNKNOWN REFUND  {u['order_no']}: rail {u['rail_total']}, store {u['store_total']} "
            f"→ {u['difference']} the store does not know about ({', '.join(u['refunds_the_store_does_not_list'])})"
        )
    for x in r["foreign"]:
        print(f"  NOT OUR ORDER   refund {x['id']} {x['amount']} on {x['refunded_transaction_id']}")
    for x in r["credits"]:
        print(f"  CREDIT          {x['id']} {x['amount']}: money out with no sale behind it")
    if not (r["unknown"] or r["foreign"] or r["credits"]):
        print("  nothing the store does not know about")
    return 0 if [u["order_no"] for u in r["unknown"]] == ["ST-1043"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
