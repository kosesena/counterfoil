# First Braintree sandbox trial (23 Oct 2026)

Scripts: `spikes/braintree_spike.py` (mocked PayPal), `spikes/braintree_card_refund_spike.py` (test card). SDK `braintree` 4.48.0. Raw output below; the transaction IDs belong to the sandbox.

## Mocked PayPal (`fake-paypal-one-time-nonce`)
```
OK   sale 40.54 via mocked PayPal: status=settling instrument=paypal_account
OK   refund 25.00 (partial)
OK   refund 25.00 again (25+25 > original)
OK   refund 120.00 (> original)
OK   refund 15.54 (exactly the remainder)
OK   refund 1.00 after fully refunded
FIND status=settling amount=40.54 refund_ids=[5 iade]
OK   vault customer … method=PayPalAccount   (fake-paypal-billing-agreement-nonce)
OK   charge 120.54 on vaulted PayPal
OK   charge 1200.54 on vaulted PayPal (10x)
OK   second sale 80.54 → refund 30.00
```
On the first run, a second sale with the same amount was rejected: `Gateway Rejected: duplicate`.

## Test card (`fake-valid-nonce`)
```
OK   card sale 40.61: status=submitted_for_settlement
FAIL refund 10.00 before settlement: 91506 Cannot refund transaction unless it is settled.
OK   testing.settle_transaction → settled
OK   refund 25.00
FAIL refund 25.00 again (total > original): 91521 Refund amount is too large.
FAIL refund 120.00 (> original): 91521 Refund amount is too large.
OK   refund 15.61 (remainder)
FAIL refund 1.00 after fully refunded: 91512 already fully refunded; 91521
```

## Findings
1. **Mocked PayPal works:** a PayPal payment, a refund, a lookup and a charge from saved PayPal (vault) can all be done in the sandbox without a PayPal account. The "not verified" item in the draft is closed.
2. **Mocked PayPal does not enforce the refund limit.** On a $40.54 transaction, $186.54 in refunds was accepted. On the card, the same requests were rejected with 91521. This is a gap in the mocked mode; we should assume PayPal refunds are limited too in the real environment. **Neither the demo nor the measurement can say "the gate caught it" by exploiting this gap in mocked PayPal.**
3. **The rail already stops these on its own (card):** a refund above the transaction amount, a refund on a fully refunded transaction, a refund on an unsettled transaction, a duplicate sale with the same amount within a short time. So the draft's "$120 refund on a $40 order" example **is already stopped by Braintree**; it cannot be shown as our difference.
4. **What the rail cannot see, and is the gate's job:**
   - A refund that stays under the total but that the customer is not owed (1 of 3 items was returned, a hidden instruction asks for the whole amount to be refunded).
   - Ownership: is the sender of the email the owner of the order? (To Braintree, a refund request is valid no matter who it comes from.)
   - A duplicate refund that stays under the total (20 + 20 on a $40 order).
   - Store rules: the return window, the human approval limit.
   - Charge amount ≠ catalog price × quantity (a $1200 charge was accepted).
5. **Design conclusion:** the basis for a refund must be the **return record (RMA)** in the store's records: which items came back, for how much. The gate compares the refund against this record; the rail already enforces the transaction-total upper limit.
