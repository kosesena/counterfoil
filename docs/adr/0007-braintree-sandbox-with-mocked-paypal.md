# 0007 · Braintree sandbox with mocked PayPal instead of the PayPal REST API

**Status:** accepted · 2026-10-23

## Context
The hackathon asks for the PayPal developer platform. PayPal accounts cannot be opened from Türkiye, where the author
lives, so the PayPal REST sandbox (Payouts, Invoicing, the Agent Toolkit) was out of reach. PayPal's developer team
answered on the hackathon Discord (22 Oct): "Braintree works!" The official rules count Braintree as a PayPal service.

## Decision
Use the Braintree sandbox through the official Python SDK, with Braintree's mocked PayPal account
(`fake-paypal-one-time-nonce`, `fake-paypal-billing-agreement-nonce`). Every sale, refund and vaulted charge in the
demo is a real sandbox transaction whose instrument is `paypal_account`. The project's story moved from paying
suppliers (Payouts) to refunds and reorders, which Braintree supports.

## Consequences
- The sandbox has no linked PayPal login, so Drop-in cannot show the PayPal login window. The demo says so and pays
  with the mocked PayPal account.
- Mocked PayPal does not enforce the refund total; cards do (error 91521). The evaluation never counts a stop that
  only the mock's gap would explain. The evaluation's in-memory rail applies the card limits instead.
- The sandbox's default merchant account settles in EUR. A USD merchant account can be set with
  `BRAINTREE_MERCHANT_ACCOUNT_ID`.
