"""Does the Braintree sandbox honour api_request_key on refund and void through the Python SDK? (26 Oct)

The GraphQL docs describe idempotency keys; the SDK accepts `api_request_key` on refund and void but says nothing about
what the gateway does with a repeated one. This sends the same refund twice with one key, then the same key with a
different amount, then a fresh key; and the same void twice with one key.
"""
import os
import random
import uuid
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


def sale(nonce):
    amount = Decimal("50.00") + Decimal(random.randint(1, 99)) / 100
    return show(f"sale {amount} ({nonce})", gw.transaction.sale({
        "amount": str(amount), "payment_method_nonce": nonce, "options": {"submit_for_settlement": True}, **account}))


print("-- refund, mocked PayPal")
t = sale("fake-paypal-one-time-nonce")
key = f"spike-refund-{uuid.uuid4().hex}"
a = show("refund 10.00, key K", gw.transaction.refund(t.id, {"amount": "10.00", "api_request_key": key}))
b = show("refund 10.00, key K again", gw.transaction.refund(t.id, {"amount": "10.00", "api_request_key": key}))
show("refund 12.00, key K (different amount)", gw.transaction.refund(t.id, {"amount": "12.00", "api_request_key": key}))
show("refund 10.00, new key", gw.transaction.refund(t.id, {"amount": "10.00", "api_request_key": key + "-2"}))
show("refund 10.00, no key", gw.transaction.refund(t.id, "10.00"))
print("     same refund id for the repeated key:", bool(a and b and a.id == b.id))
print("     refunds on the sale:", gw.transaction.find(t.id).refund_ids)

print("-- refund, card (settled first)")
c = sale("fake-valid-nonce")
gw.testing.settle_transaction(c.id)
key = f"spike-refund-{uuid.uuid4().hex}"
a = show("refund 10.00, key K", gw.transaction.refund(c.id, {"amount": "10.00", "api_request_key": key}))
b = show("refund 10.00, key K again", gw.transaction.refund(c.id, {"amount": "10.00", "api_request_key": key}))
print("     same refund id for the repeated key:", bool(a and b and a.id == b.id))
print("     refunds on the sale:", gw.transaction.find(c.id).refund_ids)

print("-- void, card (unsettled)")
v = sale("fake-valid-nonce")
key = f"spike-void-{uuid.uuid4().hex}"
show("void, key K", gw.transaction.void(v.id, {"api_request_key": key}))
show("void, key K again", gw.transaction.void(v.id, {"api_request_key": key}))
show("void, no key (already voided)", gw.transaction.void(v.id))
