# 0008 · A PayPal REST rail, so the gate sits in front of Agent Toolkit's `create_refund`

**Status:** accepted · 2026-10-24 · code and tests only; not yet run against a PayPal REST sandbox

## Context
PayPal's Agent Toolkit gives an LLM framework a `create_refund` tool. Its parameters are `capture_id`, an optional
`amount` (`currency_code`, `value`; without it the whole capture is refunded), `invoice_id` and `note_to_payer`, and
it POSTs them unchanged to `/v2/payments/captures/{capture_id}/refund` with the merchant's credentials
(`typescript/src/shared/parameters.ts` and `functions.ts` in paypal/agent-toolkit). Nothing between the model and
that call knows which items came back or who owns the order. Counterfoil only ran on Braintree ([0007](0007-braintree-sandbox-with-mocked-paypal.md)),
so the claim "the same gate fits in front of the Toolkit" was an argument, not code.

## Decision
`counterfoil/paypal.py` adds `PayPalRestRail` with the same five methods as the Braintree rails. A rail
transaction id is a PayPal capture id:

| Rail method | PayPal REST call (sandbox host only) |
|---|---|
| `refund` | `POST /v2/payments/captures/{id}/refund`, the call `create_refund` makes |
| `void` | `POST /v2/payments/authorizations/{id}/void` (a capture cannot be voided) |
| `charge` | `POST /v2/checkout/orders`, `intent: CAPTURE`, `payment_source.<paypal\|card>.vault_id` |
| `find`, `refunded_total` | `GET /v2/payments/captures/{id}`, then `GET /v2/checkout/orders/{order}` for its refunds |

`counterfoil/toolkit.py` takes `create_refund`'s own parameters, resolves the capture to the store's order, and hands
the call to the gate as a `refund`. A merchant gives the agent this function in place of the Toolkit's tool; the
PayPal keys stay with the gate ([0004](0004-the-gate-holds-the-only-rail-credentials.md)). An omitted amount is
checked as what PayPal would do with it: the order total.

- Credentials come only from `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET`; the rail refuses `PAYPAL_ENVIRONMENT`
  other than `sandbox`, and the secret is not in its repr or any error text. Without them `run_eval --rail paypal`
  stops before any model runs, and the demo stays on its other rail.
- Every money call carries a `PayPal-Request-Id`. A charge uses the store's charge request id, so the same request
  cannot be charged twice.
- A 5xx or network error raises instead of returning "failed". The gate then records the refund as `unknown` and
  keeps it counted, so a retry cannot double-refund.
- `PayPalSandboxRail` maps the fixture ids onto sandbox objects, like `SandboxRail` does for Braintree. Setup orders
  are paid with PayPal's published sandbox test card: a PayPal-wallet order needs a buyer to approve it in a browser.

## Consequences
- The tests fake the HTTP layer (`tests/test_paypal_rail.py`); CI makes no network calls. The fake follows PayPal's
  documented responses (`REFUND_AMOUNT_EXCEEDED`, `CAPTURE_FULLY_REFUNDED`, request-id idempotency). It has not been
  checked against a real REST sandbox, because the author cannot open a PayPal account from Türkiye. Anyone with
  sandbox REST credentials can run `run_eval.py --rail paypal`; until someone does, no result is claimed from it.
- The evaluation and demo checkout stay on Braintree. `DEMO_RAIL=paypal` (with the two credentials) makes the live
  demo's agent runs refund through PayPal REST instead.
- The gateway still calls the store's id field `braintree_transaction_id`; for this rail it holds a capture id.
