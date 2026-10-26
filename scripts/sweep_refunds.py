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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rail", choices=["fake", "braintree"], default="fake")
    a = ap.parse_args()

    store = Store(load_records())
    since = datetime.now(UTC) - timedelta(minutes=1)
    tag = f"sweep-{uuid.uuid4().hex[:8]}"
    rail = SandboxRail(store, tag) if a.rail == "braintree" else FakeRail.from_store(store)
    gate = Gateway(store, rail)

    args = {"order_no": "ST-1042", "rma_id": "RMA-1042", "amount": "30.00", "currency": "USD"}
    reader = {"istek": "refund", "siparis_no": "ST-1042", "tutar": "30.00", "para_birimi": "USD"}
    ctx = Context(tag, "CUS-01", frozenset({"refund"}), reader=reader)
    out = gate.handle(ctx, "refund", args)
    print(f"through the gate:  refund 30.00 on ST-1042 → {out.summary()} (rail id {out.rail and out.rail.id})")

    behind = rail.refund("fixture-txn-002", Decimal("15.00"))  # ST-1043; the store's ledger never hears of it
    print(f"behind its back:   refund 15.00 on ST-1043 → {'ok' if behind.ok else behind.error} (rail id {behind.id})")

    report = sweep(store, rail, since)
    print(f"\nsweep since {since:%Y-%m-%d %H:%M:%S} UTC: {report.seen} refund(s)/credit(s) on the rail")
    for u in report.unknown:
        print(
            f"  UNKNOWN REFUND  {u['order_no']}: rail {u['rail_total']}, store {u['store_total']} "
            f"→ {u['difference']} the store does not know about ({', '.join(u['refunds_the_store_does_not_list'])})"
        )
    for r in report.foreign:
        print(f"  NOT OUR ORDER   refund {r['id']} {r['amount']} on {r['refunded_transaction_id']}")
    for r in report.credits:
        print(f"  CREDIT          {r['id']} {r['amount']}: money out with no sale behind it")
    if report.clean:
        print("  nothing the store does not know about")
    return 0 if [u["order_no"] for u in report.unknown] == ["ST-1043"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
