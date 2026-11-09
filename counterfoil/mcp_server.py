"""counterfoil-mcp: PayPal Agent Toolkit's refund tools as an MCP server, with the gate in front of the rail.

    .venv/bin/python scripts/counterfoil_mcp.py serve --scenario P6-01               # fake rail, no keys
    .venv/bin/python scripts/counterfoil_mcp.py serve --scenario P6-01 --rail braintree  # Braintree sandbox

Any MCP client (Claude Desktop, Cursor, Claude Code) starts this over stdio and sees `create_refund` and `get_order`
with the Toolkit's names and parameters (paypal/agent-toolkit, typescript/src/shared/tools.ts and parameters.ts).
Every call goes through `Gateway.handle`; only a PASS, or a held call a human approved, reaches the rail. Behind the
Toolkit-shaped interface the rail is Braintree (sandbox) or the in-memory fake, not PayPal REST ([0007], [0009]).

The client's model reads the customer's e-mail itself, so there is no separate Reader here. The session's context is
set when the server starts, never by the model: `--scenario` takes the sender, the store's state and the Reader
hand-off from a scenario in docs/senaryolar/scenarios.json; `--customer-email` binds the sender only, and with no
hand-off every refund waits for a human (READER_INCOMPLETE).

Held calls are decided at the approval desk: a localhost-only HTTP endpoint inside this process (the gate's pending
approvals live here), with a random token. Its address and token go to a 0600 file that `counterfoil_mcp.py holds /
approve / reject` and the desk page read. No MCP tool can approve. The client never sees rail keys or the token.
"""

from __future__ import annotations

import html
import json
import logging
import os
import secrets
import threading
import uuid
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from . import toolkit
from .gateway import APPROVAL, BLOCK, MONEY_TOOLS, PASS, Context, Gateway, Outcome
from .rail import FakeRail, Rail, SandboxRail
from .scenarios import STORE_AS_OF, build, load_records, load_scenarios
from .store import Store

log = logging.getLogger("counterfoil.mcp")
DESK_FILE = Path.home() / ".counterfoil" / "mcp-desk.json"
ALL_TOOLS = frozenset({"refund", "void", "charge", "lookup_transaction"})


class Amount(BaseModel):
    currency_code: str = Field(description="Three-letter ISO 4217 currency code, e.g. USD.")
    value: str = Field(description="The amount as a decimal string, e.g. '40.00'.")


def _reasons(out: Outcome) -> list[dict]:
    return [{"code": f.code, "severity": f.severity, "detail": f.detail} for f in out.findings if f.severity != PASS]


class Session:
    """One gate, one store, one context: what the MCP tools and the approval desk share. One lock around every gate
    call, because tool calls and the manager's answers arrive on different threads."""

    def __init__(self, gate: Gateway, ctx: Context, rail_name: str):
        self.gate, self.ctx, self.rail_name = gate, ctx, rail_name
        self.lock = threading.Lock()
        self.holds: dict[str, dict] = {}  # approval id -> what the manager sees and what became of it

    @classmethod
    def create(cls, scenario_id: str | None = None, customer_email: str | None = None, rail: str = "fake") -> Session:
        if scenario_id:
            scenario = next((s for s in load_scenarios() if s["id"] == scenario_id), None)
            if scenario is None:
                raise SystemExit(f"unknown scenario {scenario_id!r}")
            store, fake, ctx = build(scenario)
        else:
            store = Store(load_records())
            fake = FakeRail.from_store(store)
            customer = store.customer_by_email(customer_email) if customer_email else None
            if customer_email and customer is None:
                raise SystemExit(f"{customer_email!r} is not a customer of the store")
            ctx = Context(
                session_id=f"mcp-{uuid.uuid4().hex[:12]}",
                customer_id=customer["customer_id"] if customer else None,
                allowed_tools=ALL_TOOLS,
                as_of=STORE_AS_OF,
            )
        chosen: Rail
        if rail == "fake":
            chosen = fake
        elif rail == "braintree":  # BraintreeRail refuses anything but BRAINTREE_ENVIRONMENT=sandbox
            chosen = SandboxRail(store, f"counterfoil-mcp-{uuid.uuid4().hex[:8]}")
        else:
            raise SystemExit(f"unknown rail {rail!r} (fake or braintree)")
        return cls(Gateway(store, chosen), ctx, rail)

    # -- the tools ---------------------------------------------------------------------------------
    def create_refund(self, params: dict) -> dict:
        with self.lock:
            out = toolkit.create_refund(self.gate, self.ctx, params)
            if out.decision == APPROVAL and out.approval_id:
                entry = self.gate.pending[out.approval_id]
                self.holds[out.approval_id] = {
                    "hold_id": out.approval_id,
                    "state": "HELD",
                    "capture_id": params.get("capture_id"),
                    "args": entry["args"],
                    "reasons": _reasons(out),
                    "note_to_payer": params.get("note_to_payer"),
                    "held_at": datetime.now(UTC).isoformat(timespec="seconds"),
                }
        return self._result(out, params.get("capture_id"))

    def get_order(self, order_id: str) -> dict:
        with self.lock:
            order = self.gate.store.orders.get(order_id) or next(
                (o for o in self.gate.store.orders.values() if o["braintree_transaction_id"] == order_id), None
            )
            out = self.gate.handle(
                self.ctx, "lookup_transaction", {"order_no": order["order_no"] if order else order_id}
            )
        if out.decision == BLOCK:
            return self._result(out, None)
        data = dict(out.data or {})
        data["capture_id"] = data.get("braintree_transaction_id")  # what create_refund takes
        return {"decision": PASS, "status": "FOUND", "order": data}

    def hold_status(self, hold_id: str) -> dict:
        with self.lock:
            hold = self.holds.get(hold_id)
        if hold is None:
            return {"status": "UNKNOWN_HOLD", "hold_id": hold_id}
        return {k: v for k, v in hold.items() if k != "args"}

    def _result(self, out: Outcome, capture_id: str | None) -> dict:
        reasons = _reasons(out)
        if out.rail_state == "unknown":
            return {
                "decision": out.decision,
                "status": "UNKNOWN",
                "findings": reasons,
                "message": "The rail did not answer; the refund may or may not have been made. Counterfoil counts it "
                "and blocks further refunds on this order until it is reconciled. Do not retry.",
            }
        if out.decision == BLOCK:
            first = next((r for r in reasons if r["severity"] == BLOCK), reasons[0] if reasons else None)
            return {
                "decision": BLOCK,
                "status": "BLOCKED",
                "rule": first and first["code"],
                "reason": first and first["detail"],
                "findings": reasons,
                "message": "Counterfoil refused this call; nothing reached the payment rail. Do not retry it as is.",
            }
        if out.decision == APPROVAL and out.rail_state == "not_called":
            return {
                "decision": APPROVAL,
                "status": "HELD_FOR_APPROVAL",
                "hold_id": out.approval_id,
                "reason": "; ".join(f"{r['code']}: {r['detail']}" for r in reasons),
                "findings": reasons,
                "message": "Held for the store manager. No money has moved. Tell the customer it is under review; "
                "get_hold_status shows the manager's answer.",
            }
        rail = out.rail
        if out.rail_state == "failed":
            return {
                "decision": out.decision,
                "status": "FAILED",
                "rail_error": rail and rail.error,
                "findings": reasons,
            }
        return {
            "decision": out.decision,
            "status": "COMPLETED",
            "id": rail and rail.id,  # the refund's Braintree transaction id (PayPal's refund id field)
            "braintree_transaction_id": rail and rail.id,
            "rail_status": rail and rail.status,
            "capture_id": capture_id,
            "rail": self.rail_name,
        }

    # -- the manager's side ------------------------------------------------------------------------
    def decide(self, hold_id: str, approve: bool) -> dict:
        with self.lock:
            hold = self.holds.get(hold_id)
            if hold is None or hold["state"] != "HELD":
                return {"status": "UNKNOWN_HOLD", "hold_id": hold_id}
            if approve:
                out = self.gate.approve(hold_id)
                result = self._result(out, hold["capture_id"])
                hold["state"] = "APPROVED" if result["status"] == "COMPLETED" else f"APPROVED_BUT_{result['status']}"
                hold["result"] = result
            else:
                self.gate.reject(hold_id)
                hold["state"] = "REJECTED"
                hold["result"] = {"status": "REJECTED", "message": "The store manager rejected this refund."}
            hold["decided_at"] = datetime.now(UTC).isoformat(timespec="seconds")
            return {k: v for k, v in hold.items() if k != "args"}

    def held(self) -> list[dict]:
        with self.lock:
            return [dict(h) for h in self.holds.values() if h["state"] == "HELD"]

    def money_calls(self) -> list[tuple]:
        return [c for c in getattr(self.gate.rail, "calls", []) if c[0] in MONEY_TOOLS]


def build_server(session: Session) -> MCPServer:
    mcp = MCPServer(
        "counterfoil",
        instructions=(
            "Refund tools named and shaped like PayPal Agent Toolkit's, with Counterfoil checking every call against "
            "the store's records before anything reaches the payment rail (Braintree sandbox). A result is PASS "
            "(refund made), HELD_FOR_APPROVAL (a store manager decides; no money moved) or BLOCKED (refused; do not "
            "retry the same call). Look the order up with get_order first: it gives the capture_id and the return "
            "record (rma_id) that create_refund should cite."
        ),
    )

    @mcp.tool(annotations=ToolAnnotations(title="Create Refund", destructive_hint=True, idempotent_hint=False))
    def create_refund(
        capture_id: str,
        amount: Amount | None = None,
        invoice_id: str | None = None,
        note_to_payer: str | None = None,
        rma_id: str | None = None,
    ) -> dict:
        """Refund a captured payment, in full or in part. Same parameters as PayPal Agent Toolkit's create_refund
        (capture_id; amount {currency_code, value}, omitted = the whole capture; invoice_id; note_to_payer), plus the
        store's return record id (rma_id), which Counterfoil checks the amount against. Every call is checked by
        Counterfoil: it may be completed, held for the store manager, or blocked."""
        params: dict = {"capture_id": capture_id}
        if amount is not None:
            params["amount"] = amount.model_dump()
        for key, value in (("invoice_id", invoice_id), ("note_to_payer", note_to_payer), ("rma_id", rma_id)):
            if value is not None:
                params[key] = value
        return session.create_refund(params)

    @mcp.tool(annotations=ToolAnnotations(title="Get Order", read_only_hint=True))
    def get_order(id: str) -> dict:  # noqa: A002 - the Toolkit's parameter name
        """Show an order: items, total, the capture_id to refund, return records (RMAs) with the amount each one
        approves, and refunds already made. `id` is the store's order number (e.g. ST-1057) or its capture id. Only
        the verified sender's own orders can be read."""
        return session.get_order(id)

    @mcp.tool(annotations=ToolAnnotations(title="Get Hold Status", read_only_hint=True))
    def get_hold_status(hold_id: str) -> dict:
        """Whether the store manager approved or rejected a refund that Counterfoil held (not a Toolkit tool)."""
        return session.hold_status(hold_id)

    return mcp


# -- approval desk ---------------------------------------------------------------------------------------------
PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Counterfoil approvals</title>
<style>body{{font:15px/1.45 system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;background:#faf7f2;
color:#2b2230}}.h{{border:1px solid #d9cfc4;border-radius:10px;padding:14px 16px;margin:12px 0;background:#fff}}
code{{background:#f1ebe4;padding:1px 4px;border-radius:4px}}button{{font:inherit;padding:6px 14px;margin-right:8px;
border-radius:6px;border:1px solid #7a4a78;cursor:pointer}}.a{{background:#7a4a78;color:#fff}}.r{{background:#fff}}
li{{margin:2px 0}}.done{{color:#6b6070}}</style>
<h1>Counterfoil · held refunds</h1><p class="done">Rail: {rail}. Session {session}.</p>{body}"""


def _hold_html(h: dict, token: str) -> str:
    a = h["args"]
    reasons = "".join(
        f"<li><code>{html.escape(r['code'])}</code> {html.escape(r['detail'])}</li>" for r in h["reasons"]
    )
    form = (
        f'<form method="post" action="/decide"><input type="hidden" name="token" value="{token}">'
        f'<input type="hidden" name="hold_id" value="{h["hold_id"]}">'
        '<button class="a" name="decision" value="approve">Approve</button>'
        '<button class="r" name="decision" value="reject">Reject</button></form>'
    )
    return (
        f'<div class="h"><b>Refund {html.escape(str(a.get("amount")))} {html.escape(str(a.get("currency")))}</b> on '
        f"order <code>{html.escape(str(a.get('order_no')))}</code>, return record "
        f"<code>{html.escape(str(a.get('rma_id') or 'none cited'))}</code><ul>{reasons}</ul>{form}</div>"
    )


class Desk:
    """Localhost-only HTTP endpoint for the manager. GET /holds and POST /holds/<id>/approve|reject take
    `Authorization: Bearer <token>`; GET /?token= and POST /decide are the same for a browser."""

    def __init__(self, session: Session, port: int = 0, desk_file: Path | None = DESK_FILE):
        self.session, self.token, self.desk_file = session, secrets.token_urlsafe(24), desk_file
        desk = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # stdout is the MCP channel; keep the desk quiet
                log.debug("desk: " + args[0], *args[1:])

            def _send(self, code: int, body: str, kind: str = "application/json"):
                data = body.encode()
                self.send_response(code)
                self.send_header("Content-Type", f"{kind}; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def _authorized(self, given: str | None) -> bool:
                return given is not None and secrets.compare_digest(given, desk.token)

            def _bearer(self) -> str | None:
                h = self.headers.get("Authorization", "")
                return h[7:] if h.startswith("Bearer ") else None

            def do_GET(self):
                url = urlparse(self.path)
                if url.path == "/":
                    if not self._authorized(parse_qs(url.query).get("token", [None])[0]):
                        return self._send(403, "forbidden", "text/plain")
                    return self._send(200, desk.page(), "text/html")
                if url.path == "/holds":
                    if not self._authorized(self._bearer()):
                        return self._send(403, '{"error": "forbidden"}')
                    return self._send(200, json.dumps(desk.session.held(), default=str))
                return self._send(404, '{"error": "not found"}')

            def do_POST(self):
                url = urlparse(self.path)
                if url.path == "/decide":
                    n = min(int(self.headers.get("Content-Length") or 0), 4096)
                    form = parse_qs(self.rfile.read(n).decode())
                    if not self._authorized(form.get("token", [None])[0]):
                        return self._send(403, "forbidden", "text/plain")
                    hold_id, decision = form.get("hold_id", [""])[0], form.get("decision", [""])[0]
                    if decision in ("approve", "reject"):
                        desk.session.decide(hold_id, decision == "approve")
                    self.send_response(303)
                    self.send_header("Location", f"/?token={desk.token}")
                    self.end_headers()
                    return None
                parts = url.path.strip("/").split("/")
                if len(parts) == 3 and parts[0] == "holds" and parts[2] in ("approve", "reject"):
                    if not self._authorized(self._bearer()):
                        return self._send(403, '{"error": "forbidden"}')
                    return self._send(
                        200, json.dumps(desk.session.decide(parts[1], parts[2] == "approve"), default=str)
                    )
                return self._send(404, '{"error": "not found"}')

        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def page(self) -> str:
        held = self.session.held()
        decided = [h for h in self.session.holds.values() if h["state"] != "HELD"]
        body = "".join(_hold_html(h, self.token) for h in held) or "<p>No refund is waiting.</p>"
        if decided:
            body += "<h2>Decided</h2>" + "".join(
                f'<p class="done"><code>{h["hold_id"][:8]}</code> {html.escape(str(h["args"].get("amount")))} '
                f"{html.escape(str(h['args'].get('currency')))} on {html.escape(str(h['args'].get('order_no')))}: "
                f"<b>{h['state']}</b> {html.escape(str((h.get('result') or {}).get('braintree_transaction_id') or ''))}</p>"
                for h in decided
            )
        return PAGE.format(rail=self.session.rail_name, session=html.escape(self.session.ctx.session_id), body=body)

    def start(self) -> Desk:
        threading.Thread(target=self.httpd.serve_forever, name="counterfoil-desk", daemon=True).start()
        if self.desk_file is not None:
            self.desk_file.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.desk_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump({"url": self.url, "token": self.token, "pid": os.getpid()}, f)
        log.info("approval desk: %s/?token=%s", self.url, self.token)
        return self

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
