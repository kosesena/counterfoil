"""Flatten saved evaluation runs into the tables the AG Studio dashboard reads.

    .venv/bin/python scripts/export_dashboard.py                       # every results/*-r3-*.jsonl
    .venv/bin/python scripts/export_dashboard.py results/2026-10-23-dev-qwen2.5-8k.jsonl

Writes dashboard/public/counterfoil-data.json with seven related tables:
runs (one per scenario × condition × repeat × model), calls (one per tool call the agent made),
findings (one per check that fired on a call), ledger (the refunds already on the order when a call
was held or blocked), scenarios, orders and returns (the store's RMA records). No LLM, no network; smoke runs under results/smoke/ are skipped by default.
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
SPENT = {"accepted", "completed", "reserved"}  # as counterfoil.store.entitlement: refunded or reserved against an RMA

# What each gate check means, in the words the dashboard shows. Unlisted codes fall back to the code itself.
CHECK_LABEL = {
    "AUTO_REFUND_LIMIT_EXCEEDED": "Above auto-refund limit",
    "CUMULATIVE_REFUND_EXCEEDS_RMA": "Refunds would exceed the RMA",
    "RMA_ALREADY_REFUNDED": "RMA already refunded",
    "RMA_AMOUNT_MISMATCH": "Amount differs from the RMA",
    "RMA_MISSING": "No RMA cited",
    "RMA_UNKNOWN": "Unknown RMA",
    "RMA_NOT_OPEN": "RMA not open",
    "SCOPE_NOT_ALLOWED": "Order outside the sender's scope",
    "CUSTOMER_ORDER_MISMATCH": "Order belongs to another customer",
    "CURRENCY_MISMATCH": "Currency differs from the order",
    "READER_INCOMPLETE": "Reader hand-off incomplete",
    "READER_CALL_MISMATCH": "Call differs from the Reader hand-off",
    "ITEMS_MISMATCH": "Items differ from the Reader hand-off",
    "CHARGE_AMOUNT_MISMATCH": "Charge differs from catalog price",
    "CHARGE_NEEDS_CONFIRMATION": "Charge needs confirmation",
    "PRIOR_BLOCKED_ATTEMPT": "Earlier blocked call in session",
    "TOOL_NOT_ALLOWED": "Tool not allowed",
    "UNKNOWN_ORDER": "Unknown order",
    "OVER_CAP": "Over the $200 cap",
    "UNRECONCILED_RAIL_REFUNDS": "Braintree shows refunds the store does not",
    "REFUND_OUTCOME_UNKNOWN": "Earlier refund outcome unknown",
    "RAIL_ITEMS_MISMATCH": "RMA exceeds Braintree's line items",
    "TRANSACTION_DISPUTED": "Open dispute on the transaction",
}


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


def charge_allowance(reader: dict, prices: dict[str, Decimal]) -> float | None:
    """Catalog price × the quantities the Reader handed off: what the store record supports for a charge."""
    try:
        return round(float(sum(prices[i["sku"]] * int(i["adet"]) for i in reader.get("kalemler") or [])), 2) or None
    except (KeyError, TypeError, ValueError):
        return None


def opening_ledger(scenario: dict, orders: dict[str, dict]) -> list[dict]:
    """Refunds and live reservations the store already holds when the run starts (baseline + the scenario's own)."""
    pre = scenario.get("preconditions", {})
    order_no = pre.get("target_attempt", {}).get("order_no") or scenario.get("ground_truth", {}).get("order_no")
    refunds = {r["refund_id"]: (no, r) for no, o in orders.items() for r in o.get("refunds", [])}
    refunds |= {r["refund_id"]: (order_no, r) for r in pre.get("required_refund_records", [])}
    rows = [
        {
            "orderNo": no,
            "rmaId": r.get("rma_id"),
            "amount": r["amount"],
            "status": r["status"],
            "source": "Store record",
        }
        for no, r in refunds.values()
    ]
    # a reservation with no refund yet is money another session is about to refund (counterfoil.store.entitlement)
    rows += [
        {
            "orderNo": r["order_no"],
            "rmaId": r.get("rma_id"),
            "amount": r["amount"],
            "status": "reserved",
            "source": "Other session",
        }
        for r in pre.get("active_reservations", [])
        if not r.get("refund_id")
    ]
    return rows


def export(paths: list[Path]) -> dict:
    scenarios = {s["id"]: s for s in load_scenarios()}
    records = load_records()
    orders = {o["order_no"]: o for o in records.get("orders", [])}
    approved = {
        (o["order_no"], ret["rma_id"]): Decimal(ret["approved_refund_amount"])
        for o in orders.values()
        for ret in o.get("returns", [])
    }
    prices = {c["sku"]: Decimal(c["unit_price"]) for c in records.get("catalog", [])}
    runs, calls, findings_rows, ledger_rows, skipped = [], [], [], [], []
    for path in paths:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            r = json.loads(line)
            if r.get("status") != "ok":
                # a run the model never finished (e.g. a timeout) has no outcome to count; it is listed, not scored
                skipped.append(
                    {
                        "source": path.stem,
                        "model": r.get("model"),
                        "scenarioId": r.get("scenario"),
                        "kind": r.get("kind"),
                        "condition": CONDITION_LABEL.get(r.get("condition"), r.get("condition")),
                        "status": r.get("status"),
                    }
                )
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
                    # genuine e-mail completed, or sent to a person (store policy: above the auto-refund limit)
                    "genuineCompleted": int(not attack and bool(s.get("legit_done"))),
                    "genuineToReview": int(not attack and not s.get("legit_done") and bool(s.get("legit_held"))),
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
            reader = r.get("reader") or {}
            ledger = opening_ledger(sc, orders)
            for i, step in enumerate(r.get("steps", [])):
                args = step.get("args") or {}
                findings = step.get("findings") or []
                money = step["tool"] in MONEY_TOOLS
                order_no, rma_id, decision = args.get("order_no"), args.get("rma_id"), step.get("decision")
                call_id = f"{run_id}/{i}"
                # what the store record allows for this call: the RMA's approved amount less what is already
                # refunded against it, or for a charge the catalog price of the items the Reader handed off
                allows = None
                if step["tool"] == "refund" and (order_no, rma_id) in approved:
                    spent = sum(
                        Decimal(str(e["amount"]))
                        for e in ledger
                        if e["orderNo"] == order_no and e["rmaId"] == rma_id and e["status"] in SPENT
                    )
                    allows = float(max(approved[order_no, rma_id] - spent, Decimal("0")))
                elif step["tool"] == "charge":
                    allows = charge_allowance(reader, prices)
                asked = amount(args.get("amount"))
                calls.append(
                    {
                        "id": call_id,
                        "runId": run_id,
                        "step": i + 1,
                        "tool": step["tool"],
                        "moneyCall": int(money),
                        "orderNo": order_no,
                        "rmaId": rma_id,
                        "amount": asked,
                        "readerAmount": amount(reader.get("tutar")) if money else None,
                        "storeAllows": allows,
                        "decision": decision,
                        "passed": int(money and decision == "PASS"),
                        "held": int(money and decision == "APPROVAL"),
                        "blocked": int(money and decision == "BLOCK"),
                        # attack-run money calls, for "attack calls: N blocked, M held of D"
                        "attackMoneyCall": int(money and attack),
                        "attackBlocked": int(money and attack and decision == "BLOCK"),
                        "attackHeld": int(money and attack and decision == "APPROVAL"),
                        "reasons": ", ".join(f["code"] for f in findings) or None,
                        "checks": ", ".join(CHECK_LABEL.get(f["code"], f["code"]) for f in findings) or None,
                        "detail": "; ".join(f["detail"] for f in findings) or None,
                        "railState": step.get("rail_state"),
                        "rail": r.get("rail", "fake"),
                        "braintreeTransaction": None,
                        "braintreeResult": None,
                    }
                )
                findings_rows += [
                    {
                        "id": f"{call_id}/{f['code']}",
                        "callId": call_id,
                        "code": f["code"],
                        "check": CHECK_LABEL.get(f["code"], f["code"]),
                        "severity": f.get("severity"),
                        "fired": 1,
                    }
                    for f in findings
                ]
                if money and decision != "PASS":
                    # the refunds already on this order when the gate held or blocked the call
                    ledger_rows += [
                        {
                            "id": f"{call_id}/ledger/{n}",
                            "callId": call_id,
                            **e,
                            "amount": amount(e["amount"]),
                            "sameRma": int(e["rmaId"] == rma_id),
                        }
                        for n, e in enumerate(x for x in ledger if x["orderNo"] == order_no)
                    ]
                if step["tool"] == "refund" and step.get("rail_state") in ("succeeded", "unknown"):
                    ledger.append(
                        {
                            "orderNo": order_no,
                            "rmaId": rma_id,
                            "amount": args.get("amount"),
                            "status": "completed" if step["rail_state"] == "succeeded" else "unknown",
                            "source": f"Agent, step {i + 1}",
                        }
                    )
                if sandbox and money and step.get("rail_state") not in (None, "not_called"):
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
    emails = {c["customer_id"]: c.get("email") for c in records.get("customers", [])}
    order_rows = [
        {
            "orderNo": o["order_no"],
            "customerId": o.get("customer_id"),
            "customerEmail": emails.get(o.get("customer_id")),
            "paymentMethod": {"paypal": "PayPal", "card": "Card"}.get(
                o.get("payment_method_type"), o.get("payment_method_type")
            ),
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
        "findings": findings_rows,
        "ledger": ledger_rows,
        "scenarios": scenario_rows,
        "orders": order_rows,
        "returns": return_rows,
        "skipped": skipped,
        "railChecks": rail_checks(),
    }


def rail_checks() -> dict | None:
    """The newest sandbox record of the rail-side checks (scripts/record_rail_checks.py), shown as it was recorded."""
    files = sorted((ROOT / "results").glob("*-braintree-rail-checks.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def main() -> None:
    # default: the 3-repeat comparison runs (one file per model); earlier 1-repeat runs stay in results/ for the record
    paths = [Path(p) for p in sys.argv[1:]] or sorted((ROOT / "results").glob("*-r3-*.jsonl"))
    data = export(paths)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"{OUT.relative_to(ROOT)}: {len(data['runs'])} runs, {len(data['calls'])} calls, {len(data['findings'])} findings, "
        f"{len(data['scenarios'])} scenarios, {len(data['orders'])} orders, {len(data['returns'])} returns from {len(paths)} file(s), {len(data['skipped'])} unfinished run(s) left out"
    )


if __name__ == "__main__":
    main()
