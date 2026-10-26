"""A sale on Braintree's dispute test card, then refunds on it (26 Oct).

Questions: how soon does the dispute show on the transaction (transaction.disputes, dispute.search), with which
status; and does Braintree itself refuse a refund on a disputed transaction, or would a refund plus the chargeback
pay the customer twice?
"""
import os
import random
import time
from decimal import Decimal

import braintree
from dotenv import load_dotenv

load_dotenv()
assert os.environ["BRAINTREE_ENVIRONMENT"] == "sandbox"

gw = braintree.BraintreeGateway(braintree.Configuration(
    environment=braintree.Environment.Sandbox,
    merchant_id=os.environ["BRAINTREE_MERCHANT_ID"],
    public_key=os.environ["BRAINTREE_PUBLIC_KEY"],
    private_key=os.environ["BRAINTREE_PRIVATE_KEY"],
))
account = {"merchant_account_id": os.environ["BRAINTREE_MERCHANT_ACCOUNT_ID"]} if os.environ.get(
    "BRAINTREE_MERCHANT_ACCOUNT_ID") else {}


def show(label, r):
    if r.is_success:
        t = r.transaction
        print(f"OK   {label}: id={t.id} type={t.type} status={t.status} amount={t.amount}")
        return t
    print(f"FAIL {label}: {'; '.join(f'{e.code} {e.message}' for e in r.errors.deep_errors) or r.message}")
    return None


amount = Decimal("60.00") + Decimal(random.randint(1, 99)) / 100
t = show(f"sale {amount} on the dispute test card", gw.transaction.sale({
    "amount": str(amount), "credit_card": {"number": "4023898493988028", "expiration_date": "12/2030"},
    "options": {"submit_for_settlement": True}, **account}))
for _ in range(10):
    disputes = gw.transaction.find(t.id).disputes
    if disputes:
        break
    time.sleep(3)
for d in disputes:
    print(f"     dispute {d.id}: status={d.status} kind={d.kind} reason={d.reason} amount={d.amount_disputed}")
found = list(gw.dispute.search(braintree.DisputeSearch.transaction_id == t.id).disputes.items)
print(f"     dispute.search by transaction id: {[(d.id, d.status) for d in found]}")
print("     transaction status:", gw.transaction.find(t.id).status)
show("settle", gw.testing.settle_transaction(t.id))
show("refund 10.00 on the disputed transaction", gw.transaction.refund(t.id, "10.00"))
show("refund the rest", gw.transaction.refund(t.id, str(amount - 10)))
