# 0001 · Trust the store's record, not the e-mail

**Status:** accepted · 2026-10-23

## Context
The attack arrives inside the customer e-mail: hidden HTML, a forged attachment line, a "corrected amount". Whatever the
agent extracts from that e-mail is attacker-controlled. In the author's graduation-thesis prototype (an ERP order
gateway), one attack only stopped by accident. The gate's checks compared the call with what an extraction step had
read from the same e-mail, so a manipulated reading passed its own consistency check.

## Options
1. Validate the call against the fields extracted from the e-mail (amount, order, items).
2. Validate the call against the store's own records: orders, return authorisations (RMA), catalog prices, completed
   and reserved refunds, which the e-mail cannot change.

## Decision
Option 2. The e-mail only proposes. A refund needs an open RMA, and the amount may not exceed what that RMA still
allows. A charge must equal catalog price × authorised quantity. The order must belong to the sender. Disagreement
between the call and the Reader's hand-off is an extra signal, never the basis.

## Consequences
- The gate is only as good as the store's records. Without an RMA there is no automatic refund, which is also how
  real shops work: the item comes back first.
- The record checks do not depend on how the instruction was hidden, so new injection styles need no new rules.
- Braintree already refuses card refunds above the transaction total. The gate does not repeat that check; it checks
  the RMA, which is the attacks' blind spot ([0003](0003-per-transaction-checks-not-a-spending-cap.md)).
