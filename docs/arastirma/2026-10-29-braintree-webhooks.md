# Braintree webhooks against a real sandbox chargeback (29 Oct 2026)

Question: when Braintree reports a chargeback, does Counterfoil lock refunds on that transaction by itself, before any
agent asks, and does the next refund get blocked?

Run: `PYTHONPATH=. .venv/bin/python spikes/braintree_webhook_spike.py` (Braintree sandbox keys from `.env`, SDK 4.48.0).
No `BRAINTREE_MERCHANT_ACCOUNT_ID` was set, so the sale settled in the sandbox default currency (EUR).

## What was real and what was simulated

| Step | Real or simulated |
|---|---|
| Sale on the dispute test card `4023898493988028` | real sandbox transaction |
| The chargeback Braintree opened on it (`transaction.find(id).disputes`) | real |
| `testing.settle_transaction` | real (sandbox test call) |
| The notification | **simulated delivery**: `webhook_testing.sample_notification(dispute_opened, <real transaction id>)`, signed with the real sandbox keys. The sample uses the transaction id as the dispute id and a fixed amount (100.00), so those two fields are not Braintree's |
| Signature check | real: `webhook_notification.parse` with the real sandbox keys, in `counterfoil/webhooks.py` and through the demo's `POST /api/braintree/webhook` |
| The next refund through the gate | real gate, real sandbox rail; blocked, so no refund call was made |

To show the webhook's lock on its own, the first gate's rail hides the disputes Braintree lists. Before the
notification only `check` ran (no refund could go out); after it, `handle` blocked.

## Output

```
REAL sale eeg4559w 80.77 EUR on the dispute test card
REAL dispute nvxm7xv26f98zt8r: chargeback open 80.77 reason=fraud
REAL settle: settled
before the webhook, check only: PASS
SIMULATED delivery, REAL keys: dispute_opened -> dispute_locked; blocked
next refund: BLOCK not_called ['TRANSACTION_DISPUTED']
refunds Braintree holds on the sale: []
the gate on the unmodified rail: ['ST-1056 has chargeback eeg4559w (open, 100.00, from webhook dispute_opened), chargeback nvxm7xv26f98zt8r (open, 80.77); answer the dispute instead of refunding']
demo endpoint: {'kind': 'dispute_opened', 'action': 'dispute_locked', 'duplicate': False}
demo endpoint, same again: {'kind': 'dispute_opened', 'action': 'dispute_locked', 'duplicate': True}
demo endpoint, payload changed: 403
demo audit: [('dispute_opened', 'eeg4559w', 'dispute_locked')]
```

- Before the notification the refund passed every check; after it, `TRANSACTION_DISPUTED` blocked it from the store's
  record alone (`rail_state` `not_called`), and the sale still has no refunds on Braintree.
- On the unmodified rail the finding lists both sources: the webhook's record and the real chargeback the rail lists.
- The demo endpoint accepted the notification once, recorded the same notification again as a duplicate, refused a
  changed payload with 403, and its audit shows one row.

## Not verified

- A real delivery from Braintree. It needs the webhook URL set in the sandbox Control Panel and a public server
  (the Render demo); instructions in `demo/README.md`. Section 4 of the live demo makes a sale on the dispute test
  card, so after that setup it should produce a real `dispute_opened` delivery, visible at `GET /api/braintree/events`.
- Which kinds the Control Panel lets a sandbox merchant subscribe to. The SDK knows `refund_failed`; the webhook docs
  read on 26 Oct do not list it (`2026-10-26-paypal-braintree-features.md`).
- Won and lost transitions from Braintree itself (tested with sample notifications only).
