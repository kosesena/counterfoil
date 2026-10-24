"""scripts/export_dashboard.py: the held-call fields the dashboard's review page and case agent read."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("export_dashboard", ROOT / "scripts" / "export_dashboard.py")
assert spec and spec.loader
export_dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_dashboard)


def run_line(scenario: str, family: str, kind: str, steps: list[dict], reader: dict | None = None) -> dict:
    return {
        "scenario": scenario,
        "kind": kind,
        "family": family,
        "condition": "counterfoil",
        "model": "test-model",
        "status": "ok",
        "reader": reader or {},
        "steps": steps,
        "score": {},
    }


def refund(amount: str, order: str, rma: str, decision: str, rail: str, findings: list[dict] | None = None) -> dict:
    return {
        "tool": "refund",
        "args": {"order_no": order, "rma_id": rma, "amount": amount},
        "decision": decision,
        "rail_state": rail,
        "findings": findings or [],
    }


def export_lines(tmp_path: Path, *lines: dict) -> dict:
    path = tmp_path / "runs.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
    return export_dashboard.export([path])


def test_reservation_from_another_session_counts_against_the_rma(tmp_path):
    finding = {"severity": "BLOCK", "code": "CUMULATIVE_REFUND_EXCEEDS_RMA", "detail": "40.00 left"}
    data = export_lines(
        tmp_path,
        run_line(
            "P6-01",
            "P6",
            "attack",
            [refund("60.00", "ST-1057", "RMA-1057", "BLOCK", "not_called", [finding])],
            {"tutar": "60.00"},
        ),
    )
    [call] = data["calls"]
    assert (call["storeAllows"], call["readerAmount"], call["amount"]) == (40.0, 60.0, 60.0)
    assert (call["blocked"], call["held"], call["blockedAmount"]) == (1, 0, 60.0)
    assert call["checks"] == "Refunds would exceed the RMA"
    assert [(e["status"], e["source"], e["amount"]) for e in data["ledger"]] == [("reserved", "Other session", 60.0)]
    assert data["findings"][0]["callId"] == call["id"]


def test_completed_refund_appears_once_and_earlier_agent_refunds_are_ledgered(tmp_path):
    data = export_lines(
        tmp_path,
        run_line(
            "P3-01",
            "P3",
            "attack",
            [
                refund(
                    "40.00",
                    "ST-1050",
                    "RMA-1050",
                    "BLOCK",
                    "not_called",
                    [{"severity": "BLOCK", "code": "RMA_ALREADY_REFUNDED", "detail": ""}],
                ),
            ],
        ),
        run_line(
            "CLEAN-01",
            "clean",
            "clean",
            [
                refund("10.00", "ST-1042", "RMA-1042", "PASS", "succeeded"),
                refund(
                    "30.00",
                    "ST-1042",
                    "RMA-1042",
                    "APPROVAL",
                    "not_called",
                    [{"severity": "APPROVAL", "code": "X_NEW", "detail": "d"}],
                ),
            ],
        ),
    )
    p3, passed, held = data["calls"]
    assert p3["storeAllows"] == 0.0
    assert [e["source"] for e in data["ledger"] if e["callId"] == p3["id"]] == ["Store record"]
    assert passed["passed"] == 1 and passed["storeAllows"] == 30.0
    assert (held["storeAllows"], held["heldAmount"], held["checks"]) == (20.0, 30.0, "X_NEW")
    assert [(e["source"], e["amount"]) for e in data["ledger"] if e["callId"] == held["id"]] == [
        ("Agent, step 1", 10.0)
    ]


def test_charge_allowance_is_catalog_price_times_reader_items():
    prices = export_dashboard.charge_allowance
    from decimal import Decimal

    catalog = {"CUP": Decimal("25.00")}
    assert prices({"kalemler": [{"sku": "CUP", "adet": 6}]}, catalog) == 150.0
    assert prices({"kalemler": [{"sku": "LAMP", "adet": 1}]}, catalog) is None
    assert prices({}, catalog) is None
