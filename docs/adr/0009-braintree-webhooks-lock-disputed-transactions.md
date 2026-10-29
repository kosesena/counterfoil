# 0009 · Braintree webhooks lock a disputed transaction before the next agent call

**Status:** accepted · 2026-10-29

## Context
The gate reads Braintree when an agent asks for money: the disputes on the transaction (`TRANSACTION_DISPUTED`), its
refunds against the ledger (`UNRECONCILED_RAIL_REFUNDS`), its line items. Between agent calls it knew nothing. A
chargeback that opens while a refund waits for the manager, or on a sale whose rail cannot list disputes (the PayPal
REST rail, a rail that has not caught up), was only found if that read happened to see it. Braintree pushes these
events as signed webhooks; the store did not listen.

## Decision
`counterfoil/webhooks.py` takes Braintree's form post (`bt_signature`, `bt_payload`), verifies it with the official
SDK (`webhook_notification.parse`, HMAC with the merchant's private key) and refuses anything that does not verify.
The demo serves it at `POST /api/braintree/webhook`.

- Every `dispute_*` notification stores the dispute's status against its transaction. The gate merges these with
  what the rail lists: the rail's status wins for a dispute it lists, a dispute only the webhook reported still counts.
  The existing rule decides: only `won` lifts the lock; `lost`, `accepted`, `auto_accepted` and `expired` keep it,
  since the chargeback has already paid the customer. Statuses apply by notification time, so a late retry of an
  older notification changes nothing.
- `refund_failed` marks the store's refund row failed (what reconciliation does); a failed refund the store never
  made is flagged.
- `transaction_settled`, `transaction_settlement_declined`, `transaction_disbursed` and `disbursement` run the
  store-wide refund sweep (`counterfoil/reconcile.py`) and flag refunds the store does not know about.
- `check` and every other kind are recorded and nothing else.
- Every verified notification gets one audit row, keyed by the sha256 of its payload; the same notification twice is
  recorded once and acted on once. `GET /api/braintree/events` lists them.

## Consequences
- A refund on a disputed transaction is blocked from the webhook alone, and a held refund approved after a chargeback
  opened is refused (approval re-runs the checks).
- Braintree sends no webhook when a refund or credit is created. A refund made in the Control Panel is still found
  only by the sweep (on a settlement or disbursement notification, or `scripts/sweep_refunds.py`) or by the gate's
  per-transaction check before the next refund on that order.
- `transaction_settled` and `transaction_settlement_declined` are only sent for some payment methods (ACH, local
  payments), not for cards or PayPal; `disbursement` is daily. For cards and PayPal the sweep trigger in practice is
  the disbursement notification.
- The hosted demo's store is a fixture with no sandbox sales behind its orders, so it does not sweep on settlement
  notifications (it records them). Dispute notifications on a judge's purchase do lock that purchase's refund runs.
- The demo keeps events in memory unless `DEMO_EVENTS_DB` names a file; the free Render instance loses them on
  restart. A real store would keep them in its own database.
- Verified for real on 29 Oct (`spikes/braintree_webhook_spike.py`, `docs/arastirma/2026-10-29-braintree-webhooks.md`):
  a sale on the dispute test card got a real open chargeback, a notification for it signed with the real sandbox keys
  locked the transaction, and the next refund was blocked with nothing sent to Braintree. Simulated: the delivery
  itself (`webhook_testing.sample_notification`), because Braintree only delivers to a public URL set in the Control
  Panel. Not yet seen: a real Braintree delivery, and which of these kinds the Control Panel offers to subscribe to.
