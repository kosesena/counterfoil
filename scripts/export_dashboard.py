"""Flatten saved evaluation runs into the tables the AG Studio dashboard reads.

    .venv/bin/python scripts/export_dashboard.py                       # every results/*-r3-*.jsonl
    .venv/bin/python scripts/export_dashboard.py results/2026-10-23-dev-qwen2.5-8k.jsonl

Writes dashboard/public/counterfoil-data.json with five related tables:
runs (one per scenario × condition × repeat × model), calls (one per tool call the agent made),
scenarios, orders and returns (the store's RMA records). No LLM, no network; smoke runs under results/smoke/ are skipped by default.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from counterfoil.scenarios import load_records, load_scenarios  # noqa: E402

OUT = ROOT / "dashboard" / "public" / "counterfoil-data.json"
CONDITION_LABEL = {"none": "No gate", "cap": "$200 cap", "counterfoil": "Counterfoil"}
MONEY_TOOLS = {"refund", "charge", "void"}


def amount(value) -> float | None:
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return None


def money_moved(score: dict) -> tuple[float, float]:
    moved = score.get("moved", {})
    refunded = sum(amount(v) or 0 for v in moved.get("refunded", {}).values())
    charged = sum(amount(c[-1] if isinstance(c, list) else c) or 0 for c in moved.get("charged", []))
    return round(refunded, 2), round(charged, 2)


def export(paths: list[Path]) -> dict:
    scenarios = {s["id"]: s for s in load_scenarios()}
    records = load_records()
    runs, calls = [], []
    for path in paths:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            r = json.loads(line)
            if r.get("status") != "ok":
                continue
            run_id = f"{path.stem}#{n}"
            s, sc = r.get("score", {}), scenarios.get(r["scenario"], {})
            refunded, charged = money_moved(s)
            attack = r["kind"] == "attack"
            runs.append(
                {
                    "id": run_id,
                    "source": path.stem,
                    "model": r["model"],
                    "scenarioId": r["scenario"],
                    "family": r["family"],
                    "kind": r["kind"],
                    "condition": CONDITION_LABEL.get(r["condition"], r["condition"]),
                    "repeat": r.get("repeat", 0),
                    "attackRun": int(attack),
                    "cleanRun": int(not attack),
                    "agentMisled": int(bool(s.get("attempt"))),  # the agent actually tried the attacker's call
                    "harm": int(bool(s.get("harm"))),  # wrong money reached the payment rail
                    "stoppedByGate": int(bool(s.get("intervention"))),
                    "stoppedByRail": int(bool(s.get("rail_refused"))),
                    "legitDone": int(bool(s.get("legit_done"))),
                    "legitHeld": int(bool(s.get("legit_held"))),
                    # clean e-mail handled right: done, or held for a human where store policy requires it (e.g. above the auto-refund limit)
                    "cleanDone": int(
                        not attack and bool(s.get("legit_done") or s.get("legit_held") or s.get("correct_abstention"))
                    ),
                    "refunded": refunded,
                    "charged": charged,
                    "steps": s.get("n_steps", len(r.get("steps", []))),
                    "agentSeconds": r.get("agent_seconds"),
                    "correctAmount": amount(sc.get("ground_truth", {}).get("correct_amount")),
                }
            )
            # Sandbox runs (--rail braintree) log [tool, fixture id, amount, sandbox txn id, sandbox result id]
            # per money call that reached the rail, in order; pair them with the steps the rail accepted.
            sandbox = [c for c in r.get("rail_money_calls", []) if len(c) >= 5]
            for i, step in enumerate(r.get("steps", [])):
                args = step.get("args") or {}
                findings = step.get("findings") or []
                calls.append(
                    {
                        "id": f"{run_id}/{i}",
                        "runId": run_id,
                        "step": i + 1,
                        "tool": step["tool"],
                        "moneyCall": int(step["tool"] in MONEY_TOOLS),
                        "orderNo": args.get("order_no"),
                        "rmaId": args.get("rma_id"),
                        "amount": amount(args.get("amount")),
                        "decision": step.get("decision"),
                        "reasons": ", ".join(f["code"] for f in findings) or None,
                        "detail": "; ".join(f["detail"] for f in findings) or None,
                        "railState": step.get("rail_state"),
                        "rail": r.get("rail", "fake"),
                        "braintreeTransaction": None,
                        "braintreeResult": None,
                    }
                )
                if sandbox and step["tool"] in MONEY_TOOLS and step.get("rail_state") not in (None, "not_called"):
                    c = sandbox.pop(0)
                    calls[-1]["braintreeTransaction"] = c[3] if step["tool"] != "charge" else None
                    calls[-1]["braintreeResult"] = c[-1] if c[-1] not in ("None", "") else None
    used = {r["scenarioId"] for r in runs}
    scenario_rows = [
        {
            "id": sid,
            "kind": s["kind"],
            "family": s["family"],
            "technique": s.get("technique"),
            "split": s["split"],
            "attackerGoal": s.get("attacker_goal"),
            "expectedDecision": s.get("expected_gateway_decision"),
            "railWouldBlock": int(bool(s.get("rail_would_block"))),
            "capWouldBlock": int(bool(s.get("cap_200_would_block"))),
        }
        for sid, s in scenarios.items()
        if sid in used
    ]
    order_rows = [
        {
            "orderNo": o["order_no"],
            "customerId": o.get("customer_id"),
            "total": amount(o.get("total")),
            "currency": o.get("currency"),
            "braintreeTransactionId": o.get("braintree_transaction_id"),
        }
        for o in records.get("orders", [])
    ]
    return_rows = [
        {
            "rmaId": ret["rma_id"],
            "orderNo": o["order_no"],
            "approvedAmount": amount(ret.get("approved_refund_amount")),
            "status": ret.get("status"),
            "items": ", ".join(f"{i['qty']}× {i['sku']}" for i in ret.get("items", [])),
        }
        for o in records.get("orders", [])
        for ret in o.get("returns", [])
    ]
    return {
        "asOf": datetime.now(UTC).isoformat(timespec="seconds"),
        "runs": runs,
        "calls": calls,
        "scenarios": scenario_rows,
        "orders": order_rows,
        "returns": return_rows,
    }


def main() -> None:
    # default: the 3-repeat comparison runs (one file per model); earlier 1-repeat runs stay in results/ for the record
    paths = [Path(p) for p in sys.argv[1:]] or sorted((ROOT / "results").glob("*-r3-*.jsonl"))
    data = export(paths)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"{OUT.relative_to(ROOT)}: {len(data['runs'])} runs, {len(data['calls'])} calls, "
        f"{len(data['scenarios'])} scenarios, {len(data['orders'])} orders, {len(data['returns'])} returns from {len(paths)} file(s)"
    )


if __name__ == "__main__":
    main()
