# 0009 · An MCP server whose tools look like Agent Toolkit's, with the gate in front of the rail

**Status:** accepted · 2026-10-29 · tests, plus one Braintree sandbox run (below)

## Context
Merchants who give an assistant money tools increasingly do it over MCP: PayPal ships `@paypal/mcp` and the Agent
Toolkit, and Claude Desktop, Cursor and Claude Code each take an MCP server with one config entry. Counterfoil only
existed as a Python library that our own two agents called ([0002](0002-two-agents-reader-and-transaction.md)), and as
a gated stand-in for Toolkit's `create_refund` ([0008](0008-paypal-rest-rail-in-front-of-agent-toolkit.md)). A client
someone else built could not use the gate.

## Decision
`counterfoil/mcp_server.py` (started by `scripts/counterfoil_mcp.py serve`) is a stdio MCP server on the official
Python SDK (`mcp` 2.3.0, `MCPServer`). It exposes:

| Tool | Shape | Goes through |
|---|---|---|
| `create_refund` | Toolkit's own: `capture_id`, `amount {currency_code, value}` (omitted = whole capture), `invoice_id`, `note_to_payer`; plus optional `rma_id` | `toolkit.create_refund` → `Gateway.handle(..., "refund", ...)` |
| `get_order` | Toolkit's own parameter, `id`; here the store's order number or its capture id | `Gateway.handle(..., "lookup_transaction", ...)`, scoped to the sender |
| `get_hold_status` | `hold_id` (not a Toolkit tool) | read-only view of what the manager decided |

Names and parameters were checked on 2026-10-29 against `typescript/src/shared/tools.ts` and `parameters.ts` in
paypal/agent-toolkit (`main`). Not mapped: `get_refund` and `list_transactions` (Toolkit ids are PayPal refund and
transaction ids; this store has Braintree ids and no listing the gate scopes yet), and every invoice, subscription,
dispute and shipment tool. The tool list of PayPal's hosted MCP server (`@paypal/mcp`) was not checked separately; its
docs page points to the same Agent Toolkit catalog.

- **Results.** PASS returns `status: COMPLETED` and the refund's Braintree transaction id. APPROVAL returns
  `status: HELD_FOR_APPROVAL`, the `hold_id` and every finding's code and detail; nothing moved. BLOCK returns
  `status: BLOCKED`, the first BLOCK rule's code and reason; nothing moved. A rail that does not answer returns
  `status: UNKNOWN` and the gate's existing freeze on that order.
- **Context is set at start, not by the model.** The client's model reads the e-mail itself, so there is no separate
  Reader. `--scenario <id>` takes the verified sender, the store's state (earlier refunds, live reservations) and the
  Reader hand-off from `docs/senaryolar/scenarios.json`. `--customer-email` binds only the sender; with no hand-off the
  gate holds every refund for a human (`READER_INCOMPLETE`). With neither, every write is refused (`NO_CONTEXT`).
- **Approvals stay outside the model.** No MCP tool approves. The gate's pending approvals live in the server process,
  so the server also runs an approval desk on `127.0.0.1` (random port, random token, both written to
  `~/.counterfoil/mcp-desk.json` with mode 0600): a small page with Approve / Reject, and the
  `counterfoil_mcp.py holds|approve|reject` commands. Approval is `Gateway.approve` as before
  ([0005](0005-approvals-are-single-use-and-bound.md)): single use, 30 minutes, re-checked, bound to the arguments.
- **Rails.** `--rail fake` (default) is the in-memory rail, no keys. `--rail braintree` loads `BRAINTREE_*` from `.env`
  and uses `SandboxRail`, which refuses anything but `BRAINTREE_ENVIRONMENT=sandbox` and maps the fixture capture ids
  onto real sandbox sales (mocked PayPal). The keys never leave the server process
  ([0004](0004-the-gate-holds-the-only-rail-credentials.md)).

## Consequences
- Behind the Toolkit-shaped interface the rail is **Braintree, not PayPal REST**. A `capture_id` here is a store
  fixture id (`fixture-txn-010`) that the server maps onto a Braintree sandbox sale; a refund id is a Braintree
  transaction id. A `--rail paypal` option on `PayPalSandboxRail` is not built; that rail has never been run against
  a real REST sandbox ([0008](0008-paypal-rest-rail-in-front-of-agent-toolkit.md)).
- The desk is only as separate from the model as the client's sandbox. Claude Desktop's model has no shell; Claude
  Code's does, so it could run `counterfoil_mcp.py approve` itself. `docs/mcp.md` gives the permission rule that denies
  it there.
- `--scenario` hand-offs are the scenario's recorded Reader contract, not a Reader that read the pasted text. A pasted
  e-mail that differs from the scenario's makes the gate hold the call (`READER_CALL_MISMATCH`), which is the safe side.
- One server process is one session (one inbound case). A second server overwrites the desk file; the CLI then talks
  to the newer one.

## Verified
- Tests (`tests/test_mcp_server.py`, no network): the listing and its schemas, PASS / APPROVAL / BLOCK through an MCP
  client, P6-01 block → hold → desk approval → refund, rejection, single use, token, file mode, and the script over
  real stdio with nothing but MCP on stdout.
- Braintree sandbox, 2026-10-29, over stdio with `--rail braintree` (script and log kept outside the repo):
  - CLEAN-01, `create_refund(fixture-txn-001, USD 30.00, RMA-1042)` → PASS, refund **`9xx4kh8b`** (credit 30.00 of
    setup sale `bh50r7p9`, mocked PayPal, `settling`).
  - P6-01: `create_refund` USD 60.00 on RMA-1057 → BLOCK `CUMULATIVE_REFUND_EXCEEDS_RMA` (60 reserved + 60 > 100), no
    rail call; USD 40.00 → held (`READER_CALL_MISMATCH`, `PRIOR_BLOCKED_ATTEMPT`); approved at the desk → refund
    **`5qh59v54`** (credit 40.00 of setup sale `1qdey329`).
  - The sandbox's default merchant account settles in **EUR**, so both credits read 30.00 / 40.00 EUR although the
    store and the tool call say USD ([0007](0007-braintree-sandbox-with-mocked-paypal.md)). The earlier USD 60.00 in
    P6-01 is a reservation in the store only; it was not made in the sandbox.
- Not verified: a session in Claude Desktop, Cursor or Claude Code itself (the tests use the SDK's own client), and
  any PayPal REST call.
