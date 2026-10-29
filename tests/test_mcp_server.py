"""counterfoil-mcp over the MCP protocol (in-process client, no network): the Toolkit-shaped tools, PASS / APPROVAL /
BLOCK results, the HOMI P6-01 story end to end, and the approval desk that is the only way to release a hold."""

import asyncio
import json
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

import pytest
from mcp import Client

from counterfoil.mcp_server import Desk, Session, build_server

CLEAN_01 = {"capture_id": "fixture-txn-001", "amount": {"currency_code": "USD", "value": "30.00"}, "rma_id": "RMA-1042"}


def usd(value):
    return {"currency_code": "USD", "value": value}


def run(session, *calls):
    """Connect an MCP client to the server and make the calls; returns the tool listing and each parsed result."""

    async def go():
        async with Client(build_server(session)) as client:
            tools = (await client.list_tools()).tools
            results = []
            for name, args in calls:
                r = await client.call_tool(name, args)
                assert not r.is_error, r
                results.append(json.loads(r.content[0].text))
            return tools, results

    return asyncio.run(go())


@pytest.fixture
def desk(tmp_path):
    started = []

    def make(session):
        d = Desk(session, desk_file=tmp_path / "desk.json").start()
        started.append(d)
        return d

    yield make
    for d in started:
        d.stop()


def call_desk(desk, method, path, token=None):
    req = urllib.request.Request(  # noqa: S310 - the test's own 127.0.0.1 desk
        desk.url + path, method=method, headers={"Authorization": f"Bearer {token or desk.token}"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:  # noqa: S310 - the test's own 127.0.0.1 desk
        return json.loads(r.read())


# -- the tool listing ------------------------------------------------------------------------------------------------
def test_tools_carry_the_toolkit_names_and_parameters():
    tools, _ = run(Session.create("CLEAN-01"))
    by_name = {t.name: t for t in tools}
    assert set(by_name) == {"create_refund", "get_order", "get_hold_status"}  # nothing that could approve
    refund = by_name["create_refund"].input_schema
    assert refund["required"] == ["capture_id"]
    assert {"capture_id", "amount", "invoice_id", "note_to_payer", "rma_id"} == set(refund["properties"])
    assert set(refund["$defs"]["Amount"]["properties"]) == {"currency_code", "value"}
    assert by_name["get_order"].input_schema["required"] == ["id"]
    assert by_name["create_refund"].annotations.destructive_hint
    assert by_name["get_order"].annotations.read_only_hint


# -- PASS / APPROVAL / BLOCK -----------------------------------------------------------------------------------------
def test_pass_returns_the_rail_transaction_id():
    session = Session.create("CLEAN-01")
    _, [out] = run(session, ("create_refund", CLEAN_01))
    assert out["decision"] == "PASS" and out["status"] == "COMPLETED"
    assert out["braintree_transaction_id"] == "fake-refund-1" and out["capture_id"] == "fixture-txn-001"
    assert session.money_calls() == [("refund", "fixture-txn-001", Decimal("30.00"))]


def test_approval_returns_the_hold_id_and_reason_and_moves_nothing():
    session = Session.create("CLEAN-01")
    _, [out] = run(session, ("create_refund", {"capture_id": "fixture-txn-001", "amount": usd("30.00")}))
    assert out["decision"] == "APPROVAL" and out["status"] == "HELD_FOR_APPROVAL"
    assert len(out["hold_id"]) == 32 and "RMA_MISSING" in out["reason"]
    assert session.money_calls() == []


def test_block_returns_the_rule_code_and_reason():
    session = Session.create("P6-01")
    _, [out] = run(
        session, ("create_refund", {"capture_id": "fixture-txn-010", "amount": usd("60.00"), "rma_id": "RMA-1057"})
    )
    assert out["decision"] == "BLOCK" and out["status"] == "BLOCKED"
    assert out["rule"] == "CUMULATIVE_REFUND_EXCEEDS_RMA" and "40.00 left" in out["reason"]
    assert session.money_calls() == []


def test_unknown_capture_is_blocked_before_the_rail():
    session = Session.create("CLEAN-01")
    _, [out] = run(session, ("create_refund", {"capture_id": "5TY05013RG002845M", "amount": usd("1.00")}))
    assert out["rule"] == "UNKNOWN_CAPTURE" and session.money_calls() == []


def test_get_order_gives_the_capture_and_return_record_for_the_sender_only():
    session = Session.create("P6-01")  # sender CUS-05
    _, [mine, by_capture, theirs] = run(
        session,
        ("get_order", {"id": "ST-1057"}),
        ("get_order", {"id": "fixture-txn-010"}),
        ("get_order", {"id": "ST-1042"}),
    )
    assert mine["order"]["capture_id"] == "fixture-txn-010"
    assert mine["order"]["returns"][0]["rma_id"] == "RMA-1057"
    assert by_capture["order"]["order_no"] == "ST-1057"
    assert theirs["decision"] == "BLOCK" and theirs["rule"] == "SCOPE_NOT_ALLOWED" and "order" not in theirs


def test_without_a_verified_sender_every_refund_is_refused():
    session = Session.create()
    _, [out] = run(session, ("create_refund", CLEAN_01))
    assert out["rule"] == "NO_CONTEXT" and session.money_calls() == []


def test_without_a_reader_hand_off_a_correct_refund_still_waits_for_a_human():
    session = Session.create(customer_email="mira.velden@example.com")
    _, [out] = run(session, ("create_refund", CLEAN_01))
    assert out["status"] == "HELD_FOR_APPROVAL" and "READER_INCOMPLETE" in out["reason"]


# -- HOMI P6-01 end to end through the desk --------------------------------------------------------------------------
def test_p6_01_block_then_hold_then_manager_approves_the_remainder(desk):
    session = Session.create("P6-01")
    d = desk(session)
    _, [blocked, held] = run(
        session,
        ("create_refund", {"capture_id": "fixture-txn-010", "amount": usd("60.00"), "rma_id": "RMA-1057"}),
        ("create_refund", {"capture_id": "fixture-txn-010", "amount": usd("40.00"), "rma_id": "RMA-1057"}),
    )
    assert blocked["rule"] == "CUMULATIVE_REFUND_EXCEEDS_RMA"
    assert held["status"] == "HELD_FOR_APPROVAL" and "PRIOR_BLOCKED_ATTEMPT" in held["reason"]
    assert [h["hold_id"] for h in call_desk(d, "GET", "/holds")] == [held["hold_id"]]
    assert session.money_calls() == []

    decided = call_desk(d, "POST", f"/holds/{held['hold_id']}/approve")
    assert decided["state"] == "APPROVED" and decided["result"]["braintree_transaction_id"] == "fake-refund-1"
    _, [status] = run(session, ("get_hold_status", {"hold_id": held["hold_id"]}))
    assert status["state"] == "APPROVED"
    assert [c[:3] for c in session.money_calls()] == [("refund", "fixture-txn-010", Decimal("40.00"))]
    # single use: a second approval does nothing
    assert call_desk(d, "POST", f"/holds/{held['hold_id']}/approve")["status"] == "UNKNOWN_HOLD"
    assert len(session.money_calls()) == 1


def test_a_rejected_hold_never_reaches_the_rail(desk):
    session = Session.create("CLEAN-01")
    d = desk(session)
    _, [held] = run(session, ("create_refund", {"capture_id": "fixture-txn-001", "amount": usd("30.00")}))
    assert call_desk(d, "POST", f"/holds/{held['hold_id']}/reject")["state"] == "REJECTED"
    _, [status] = run(session, ("get_hold_status", {"hold_id": held["hold_id"]}))
    assert status["state"] == "REJECTED" and session.money_calls() == []


def test_the_desk_needs_its_token_and_writes_it_privately(desk, tmp_path):
    session = Session.create("CLEAN-01")
    d = desk(session)
    _, [held] = run(session, ("create_refund", {"capture_id": "fixture-txn-001", "amount": usd("30.00")}))
    with pytest.raises(urllib.error.HTTPError) as exc:
        call_desk(d, "POST", f"/holds/{held['hold_id']}/approve", token="wrong")
    assert exc.value.code == 403 and session.money_calls() == []
    assert d.httpd.server_address[0] == "127.0.0.1"
    f = tmp_path / "desk.json"
    assert f.stat().st_mode & 0o077 == 0 and json.loads(f.read_text())["token"] == d.token


def test_the_desk_page_approves_with_a_form(desk):
    session = Session.create("CLEAN-01")
    d = desk(session)
    _, [held] = run(session, ("create_refund", {"capture_id": "fixture-txn-001", "amount": usd("30.00")}))
    with urllib.request.urlopen(f"{d.url}/?token={d.token}", timeout=5) as r:  # noqa: S310
        page = r.read().decode()
    assert held["hold_id"] in page and "RMA_MISSING" in page
    body = f"token={d.token}&hold_id={held['hold_id']}&decision=approve".encode()
    with urllib.request.urlopen(urllib.request.Request(f"{d.url}/decide", data=body, method="POST"), timeout=5):  # noqa: S310
        pass
    assert session.holds[held["hold_id"]]["state"] == "APPROVED" and len(session.money_calls()) == 1


# -- the rail --------------------------------------------------------------------------------------------------------
def test_braintree_rail_refuses_anything_but_the_sandbox(monkeypatch):
    monkeypatch.setenv("BRAINTREE_ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="sandbox"):
        Session.create("CLEAN-01", rail="braintree")


def test_the_script_speaks_mcp_on_stdio_with_nothing_else_on_stdout(tmp_path):
    """What Claude Desktop does: launch the script and talk over its stdin/stdout. Logs must stay on stderr."""
    import sys

    from mcp import StdioServerParameters

    server = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).resolve().parent.parent / "scripts" / "counterfoil_mcp.py"),
            "serve",
            "--scenario",
            "P6-01",
        ],
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )

    async def go():
        async with Client(server) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            r = await client.call_tool(
                "create_refund", {"capture_id": "fixture-txn-010", "amount": usd("60.00"), "rma_id": "RMA-1057"}
            )
            return names, json.loads(r.content[0].text)

    names, out = asyncio.run(go())
    assert "create_refund" in names and out["rule"] == "CUMULATIVE_REFUND_EXCEEDS_RMA"
    assert json.loads((tmp_path / ".counterfoil" / "mcp-desk.json").read_text())["url"].startswith("http://127.0.0.1:")
