# 0002 · Two agents: a tool-less Reader and a Transaction agent that never sees the e-mail

**Status:** accepted · 2026-10-22

## Context
A single agent that reads the e-mail and holds the payment tools gives an injected instruction a direct path to money.

## Options
1. One agent with tools, hardened by its prompt.
2. Split the work (the Dual LLM pattern, CaMeL). A Reader with no tools turns the raw e-mail into a fixed set of
   fields. A Transaction agent sees only those fields and calls the tools.

## Decision
Option 2. The hand-off schema is fixed: e-mail, order, RMA, request type, amount, currency, items, and a free-text
`note`. The Transaction agent never sees the e-mail, and the sender identity comes from the envelope, not from either
model.

## Consequences
- The `note` field is the known weak point of this pattern, so it is tested on purpose (attack family P4).
- The split narrows the path but does not close it. The measurements still show the Transaction agent being misled
  through the hand-off. That is why the gate ([0001](0001-trust-the-store-record-not-the-email.md)) is the control,
  and the split is a second layer.
- Prompts are deliberately not hardened against injection: the evaluation measures the gate, not prompt craft.
