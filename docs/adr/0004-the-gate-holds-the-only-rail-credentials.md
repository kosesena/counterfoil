# 0004 · The gate holds the only payment-rail credentials

**Status:** accepted · 2026-10-22

## Context
A gate that can be bypassed is advice, not a control. If the agent process can reach Braintree directly, one injected
call around the gate is enough.

## Decision
Only the gate holds the Braintree keys. The agents get tool names, and every tool call is a request to the gate. The
rail adapter refuses to start unless `BRAINTREE_ENVIRONMENT=sandbox`. In the live demo the keys live in the server's
environment, are redacted from every response, and never reach the browser.

## Consequences
- Every money movement has one choke point and one log, which is also where the dashboard reads its data.
- The demo's checkout replays recorded agent calls through the same gate onto a real sandbox transaction, so the public
  page can move sandbox money without exposing a model or a key.
