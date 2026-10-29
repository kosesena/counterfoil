"""Record, on the Braintree sandbox, the rail-side checks the dashboard shows next to the evaluation.

Two things, both real sandbox calls:
- the store-wide refund sweep (scripts/sweep_refunds.py): one refund through the gate, one straight on Braintree
  behind its back, then one transaction.search; the second refund is what the sweep must report;
- what Braintree refuses on its own (the live demo's section 4, demo/checkout.py rail_rules): a test card settled with
  testing.settle_transaction, mocked PayPal, and the dispute test card next to the gate's check.

    .venv/bin/python scripts/record_rail_checks.py     # needs BRAINTREE_* in .env; writes results/<date>-braintree-rail-checks.json

scripts/export_dashboard.py puts the newest such file into the dashboard data as `railChecks`.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from demo.checkout import Checkout  # noqa: E402
from scripts.sweep_refunds import run as sweep_run  # noqa: E402


def main() -> int:
    now = datetime.now(UTC)
    record = {
        "recordedAt": now.isoformat(timespec="seconds"),
        "rail": "braintree-sandbox",
        "sweep": sweep_run("braintree"),
        "railRules": Checkout(True).rail_rules(),
    }
    out = ROOT / "results" / f"{now:%Y-%m-%d}-braintree-rail-checks.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    found = [u["order_no"] for u in record["sweep"]["unknown"]]
    print(
        f"{out.relative_to(ROOT)}: sweep found {found}; rail rules {[len(v) for v in record['railRules'].values()]} steps"
    )
    return 0 if found == ["ST-1043"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
