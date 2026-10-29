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

## Real delivery from Braintree (29 Oct, 19:01–19:03 UTC)

After the merge Render deployed the endpoint, and the webhook was created in the sandbox Control Panel (API →
Webhooks) for `https://counterfoil-demo.onrender.com/api/braintree/webhook`.

- **Kinds the Control Panel offers** a sandbox merchant: Subscription (8), Dispute (Accepted, Auto Accepted, Disputed,
  Expired, Lost, Opened, Under Review, Won), Disputed Transaction (Custom field updated), Payment Method (2) and
  Refund (Refund Failed). No transaction settlement, disbursement or refund-created kinds. Subscribed: the eight
  dispute kinds and Refund Failed.
- **Check URL**: Braintree's own `check` notification arrived at 19:01:49, verified, recorded as `checked`.
- **Real chargeback, real delivery**: section 4 of the live demo (`POST /api/checkout/rail-rules`) made a sale of
  80.14 on the dispute test card (`1w71eq0n`); Braintree opened chargeback `y6c5t9nsm7834gnt` (open, fraud), sent
  `dispute_opened` at 19:02:40, and the demo received it at 19:02:42: verified, action `dispute_locked`, refunds on
  `1w71eq0n` blocked. Nothing about this delivery was simulated.
- In the same section the gate blocked a refund of 40.00 on the sale, and Braintree alone accepted it (`7fjkz5he`).
  That refund went straight to Braintree, outside the gate, as the section is meant to show.
- When the dispute event arrived the earlier `check` row was no longer listed: the demo keeps events in memory, so
  the process restarted or a second instance answered in between. A file in `DEMO_EVENTS_DB` on a persistent disk
  would keep them.

- **Second real delivery** (19:16, after the demo panel was deployed): sale `ha8mrjw1`, chargeback
  `hbvxshgxcph3pp39` created 19:16:03; Braintree's notification is stamped 19:16:18 but reached the demo at 19:20:36,
  about four minutes later; verified, `dispute_locked`. Whether a first attempt failed (the deploy had just switched
  instances) or Braintree delayed it is not known. The demo page now keeps checking for ten minutes.

## Still not verified

- Won and lost transitions sent by Braintree itself (tested with sample notifications only).
- A real `refund_failed` delivery.
- The settlement and disbursement handling: the Control Panel does not offer those kinds to this merchant, so in
  practice the sweep runs from `scripts/sweep_refunds.py` and the gate's per-transaction check, not from a webhook.
