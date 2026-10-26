# Threat model

What Counterfoil protects, from whom, where the trust boundaries are, and which attacks it stops and which it
cannot. Code references point at [`counterfoil/gateway.py`](../counterfoil/gateway.py) unless noted; the attack
families P1–P7 are the ones in [`docs/senaryolar/scenarios.json`](senaryolar/scenarios.json).

## System in one picture

```
                      untrusted                          ┊                 trusted (merchant side)
                                                         ┊
 customer / attacker ──e-mail──▶ Reader agent (LLM, no tools) ──structured hand-off──┐
                                                         ┊                           ▼
                                  Transaction agent (LLM, tools, never sees the e-mail) ──tool call──▶ GATE ──▶ rail (Braintree sandbox)
                                                         ┊                           ▲        │           ▲
                                                         ┊             store records (orders, RMAs,      │
                                                         ┊             catalog, refunds, charges)  held calls
                                                         ┊                                          ▼
                                                         ┊                                       manager (human)
```

The gate is the only component that holds rail credentials ([ADR 0004](adr/0004-the-gate-holds-the-only-rail-credentials.md)).
Both agents are treated as untrusted: they process attacker-controlled text, so any tool call they produce may be the
attacker's.

## Assets

| Asset | Why it matters |
|---|---|
| Merchant money on the rail | Refunds, voids and charges are irreversible once settled. |
| Customers' vaulted payment methods | A charge on a saved method needs no card entry, so it is the cheapest thing to abuse. |
| Customer and order data | `lookup_transaction` returns order details; other customers' data must not leak. |
| Rail credentials (Braintree keys) | Whoever holds them can move money without the gate. |
| Store records (orders, return records, catalog, refund ledger) | The gate's source of truth. If they are wrong, the gate is wrong. |
| Pending approvals | A held call that executes later must be exactly what the manager approved. |

## Actors

| Actor | Trust | Capabilities |
|---|---|---|
| **Customer** | Authenticated by the mailbox envelope only | Sends e-mail. Their customer id is resolved by the system from the sender address ([`Context`](../counterfoil/gateway.py), `Store.customer_by_email` in [`store.py`](../counterfoil/store.py)), never by an LLM. |
| **Attacker e-mail** | Untrusted | Any text, hidden HTML, quoted threads, attachments. May come from a real customer's address (a customer attacking the shop) or carry instructions aimed at the agents (prompt injection). |
| **Reader agent** | Untrusted output | Reads the e-mail, has no tools, returns fixed fields (`istek`, `siparis_no`, `iade_kaydi_no`, `tutar`, `para_birimi`, `kalemler`) plus a free-text `note`. Can be misled. |
| **Transaction agent** | Untrusted output | Never sees the e-mail; gets the hand-off and the tools `refund`, `charge`, `void`, `lookup_transaction`. Can be misled through the hand-off, especially the `note`. |
| **Gate** | Trusted | Decides PASS / APPROVAL / BLOCK per call against the store records; holds the rail keys; keeps the log. |
| **Rail** | Trusted to execute, not to judge | Braintree sandbox. Refuses some things (over-total card refunds, unsettled refunds, duplicate sales) but knows nothing about return records or who owns an order. Mocked PayPal does not even enforce the refund total ([braintree experiment](arastirma/2026-10-23-braintree-deneme.md)). |
| **Manager** | Trusted, fallible | Approves or rejects held calls. Sees the findings; can still approve a bad call. |

## Trust boundaries

1. **E-mail → Reader.** Everything in the e-mail is attacker-controlled. The Reader's output is structured, but its
   *values* are only as good as the Reader's reading.
2. **Reader → Transaction agent.** Fixed fields plus a free-text `note`; the `note` is the main path for smuggled
   instructions (P4). The split narrows the path, it does not close it ([ADR 0002](adr/0002-two-agents-reader-and-transaction.md)).
3. **Transaction agent → gate.** Every tool call crosses here. The gate never reads the e-mail; it compares the call
   with the records and with the Reader's fixed fields ([ADR 0001](adr/0001-trust-the-store-record-not-the-email.md),
   [ADR 0006](adr/0006-check-what-the-call-does-not-what-the-text-says.md)).
4. **Gate → rail.** Only executed calls cross. Credentials stay on the gate side.
5. **Gate → manager → gate.** A held call returns only through `Gateway.approve`, single-use and bound to the call
   ([ADR 0005](adr/0005-approvals-are-single-use-and-bound.md)).

## What the gate stops, per family

| Family | Attack (dev / holdout scenario) | What stops it | Decision | Code |
|---|---|---|---|---|
| **P1** amount or currency override | Refund 60 against a 30 RMA (P1-01); refund in EUR on a USD order (P1-02) | Amount above the return record's remaining entitlement; currency differs from the order | APPROVAL (`RMA_AMOUNT_MISMATCH`, `CURRENCY_MISMATCH`) | `Gateway._check_refund` |
| **P2** someone else's order | CUS-01 refunds CUS-02's order (P2-01); near-match order number (P2-02) | The order's owner in the store record is not the envelope sender | APPROVAL (`CUSTOMER_ORDER_MISMATCH`); reads: BLOCK (`SCOPE_NOT_ALLOWED`) | `_check_refund`, `_check_void`, `_check_lookup` |
| **P3** replay | Repeat an already-paid RMA refund (P3-01); retry a refund whose outcome is unknown (P3-02) | RMA status `refunded`; any `pending`/`unknown` refund on the order blocks new refunds until reconciled; the rail showing refunds the store does not know about blocks too | BLOCK (`RMA_ALREADY_REFUNDED`, `REFUND_OUTCOME_UNKNOWN`, `UNRECONCILED_RAIL_REFUNDS`) | `_check_refund`, `_rail_drift`, `Store.entitlement` |
| **P4** instruction smuggled through the Reader's `note` | Raise 30 → 50 (P4-01), 25 → 40 (P4-02) | The call differs from the Reader's fixed fields | APPROVAL (`READER_CALL_MISMATCH`) | `Gateway._reader_check` |
| **P5** tool or scope escalation | Unlisted export tool (P5-01); lookup of another customer's order (P5-02) | Tool allowlist per session; reads scoped to the sender's orders; every later money call in that session is held | BLOCK (`TOOL_NOT_ALLOWED`, `SCOPE_NOT_ALLOWED`), then APPROVAL (`PRIOR_BLOCKED_ATTEMPT`) | `Gateway.check`, `_check_lookup` |
| **P6** split refund | 60 + 60 against a 100 RMA, across calls (P6-01) or sessions (P6-02) | Remaining entitlement counts completed refunds *and* live reservations; check-and-reserve is one SQLite transaction | BLOCK (`CUMULATIVE_REFUND_EXCEEDS_RMA`, `CONCURRENT_REFUND`) | `_check_refund`, `_execute_refund`, `Store.transaction` |
| **P7** reorder quantity inflation | Charge 150 instead of 25 (P7-01), 160 instead of 80 (P7-02) | No store record says how many the customer ordered, so every charge is held for a human to confirm the itemised total; it must also equal catalog price × the Reader's quantity, use the sender's own vaulted method, once per e-mail | APPROVAL (`CHARGE_NEEDS_CONFIRMATION`, `CHARGE_AMOUNT_MISMATCH`, `ITEMS_MISMATCH`); BLOCK (`PAYMENT_METHOD_NOT_OWNED`, `DUPLICATE_CHARGE`) | `Gateway._check_charge`, `_execute_charge` |

Cross-cutting guarantees, each with tests in `tests/test_gateway_mechanics.py` and property tests in
`tests/test_gateway_properties.py`:

- A BLOCKed call never reaches the rail (`Gateway.handle`).
- An approval executes at most once, within 30 minutes, only for the exact arguments it was issued for, and only if
  the refund state has not moved since the manager looked (`Gateway.approve`, `_execute_refund`).
- Amounts are parsed strictly as `Decimal` with at most two decimals; floats, `1e3`, `30,00`, negatives and zero are
  refused (`parse_amount` in [`money.py`](../counterfoil/money.py)).
- An exception from the rail is recorded as outcome *unknown* and keeps the money counted, so a retry cannot double-pay
  (`Gateway._call`, `_execute_refund`).
- Every refund and void carries a rail idempotency key (Braintree `api_request_key`, PayPal `PayPal-Request-Id`)
  derived from the transaction, order, RMA, amount and what the RMA had already refunded. Two gate processes that both
  passed the check before either refund landed send the same key and the rail pays once (`request_key`; sandbox
  behaviour in `spikes/braintree_request_key_spike.py`).

## What the gate cannot stop

These are limits of the design, not bugs. They are listed so nobody reads the measured results as more than they are.

1. **A call the records allow passes, by definition.** If an attacker gets a return record opened (a real return at the
   HOMI station, a careless support agent), a refund up to that record's amount to the order's owner is legitimate as
   far as the gate can tell. The gate bounds the loss to what the store itself authorised; it does not judge whether
   the store should have authorised it.
2. **For a charge, the human is the control.** For refunds the bound comes from the store (the RMA). For a reorder
   there is no store-side record of what the customer wants: the only source is the e-mail, through the Reader. A
   qwen3 run showed the Reader itself following hidden HTML (6 × CUP instead of 1), after which call, Reader and
   catalog all agreed. So every charge is now held (`CHARGE_NEEDS_CONFIRMATION`) with the itemised total spelled out;
   the gate cannot tell a genuine "six cups" from an injected one, and a confirmer who does not check the basket
   against the customer gets what they confirmed. The cost is that genuine reorders wait for a human too. The money
   can still only go to the sender's own vaulted method, at catalog prices, once per e-mail.
3. **APPROVAL is not BLOCK.** A held call executes if the manager approves it. The findings tell the manager what is
   wrong; a manager who approves anyway gets what they approved (bound to those exact arguments, once).
4. **Sender identity is the mailbox's job.** The customer id comes from the envelope sender. A spoofed sender address
   that the mail system accepts (no SPF/DKIM/DMARC enforcement) is a different customer as far as the gate knows.
   The demo has no real mailbox; this is an assumption about the deployment.
5. **The store records are trusted.** Anyone who can write orders, return records, the catalog or the refund ledger
   controls the gate's decisions. Protecting that database is outside the gate.
6. **What the agents *say* is not gated.** The gate checks tool calls. A misled agent can still write a misleading reply
   e-mail; it cannot attach other customers' data to it because reads are scoped, but tone and promises are unchecked.
7. **Approvals live in memory.** Pending approvals are lost on restart (fail closed: the manager has to re-request).
   The refund ledger and reservations are in SQLite and survive.
8. **Denial of service on oneself.** An attacker who triggers one BLOCK in a session makes every later money call in
   that session wait for a human (`PRIOR_BLOCKED_ATTEMPT`). That is intended, but it does cost the genuine customer time.
9. **The rail stand-in is not the rail.** The measured results use `FakeRail`, an in-memory model of the card limits we
   observed in the sandbox. `--rail braintree` exercises the real sandbox; mocked PayPal refunds above the transaction
   total, which cards refuse, and we never count that as a gate catch.

## Live demo (`demo/`)

Additional assets: the Braintree sandbox keys and the model API key in the server environment, and the operator's
model budget.

- Keys stay in the environment and are redacted from every response (`demo/app.py`, `redact`).
- The rail is wrapped so a run can only touch the fixture store's own transaction ids and vaulted tokens, whatever the
  agent names and whatever the gate condition (`demo/scope.py`).
- Live mode is rate-limited per IP and capped per day; request bodies are size-limited (`demo/limits.py`,
  `demo/app.py`). Replay mode serves saved runs and is not metered.
- Not covered: the hosting platform, TLS termination and the proxy headers it forwards.
