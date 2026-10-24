# 0003 · Per-transaction record checks instead of a spending cap

**Status:** accepted · 2026-10-23

## Context
Most agent-payment guards in the market are generic: a per-transaction cap, a tool allowlist, a signed intent
(IntentGuard, AgentGuard, Countersign, AgentCore, AP2; see `docs/arastirma/2026-10-23-rakipler.md`). The attacks that
matter for a shop stay small. An over-refund below the order total, a split refund, or a replay of an already-paid
refund passes a cap and passes Braintree's own limits.

## Options
1. A cap plus allowlist (what most projects ship).
2. Per-transaction checks against the record ([0001](0001-trust-the-store-record-not-the-email.md)), with cumulative
   accounting across calls and sessions.

## Decision
Option 2, measured against option 1. The evaluation runs every scenario under three conditions: no gate, a $200 cap,
and Counterfoil.

## Consequences
- Refunds are counted per RMA across calls and sessions, including reserved and in-flight amounts. This is what stops
  P6 (two $60 refunds against a $100 return).
- Evidence: in every model measured so far, the $200 cap stopped none of the attacks that misled the agent. Counterfoil
  let none of them move money (README, "Measured results").
- The cap stays useful as a policy (big refunds need staff review), so it is kept inside Counterfoil as an
  auto-refund limit, not as the defence.
