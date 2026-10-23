"""Braintree sandbox spike: what does the payment rail itself enforce?

Run: .venv/bin/python spikes/braintree_spike.py
Needs .env with BRAINTREE_* sandbox keys. Sandbox only: uses test nonces and testing.settle.
"""
import os
import random
from decimal import Decimal

import braintree
from dotenv import load_dotenv

load_dotenv()
assert os.environ["BRAINTREE_ENVIRONMENT"] == "sandbox", "spike runs against sandbox only"

gw = braintree.BraintreeGateway(braintree.Configuration(
    environment=braintree.Environment.Sandbox,
    merchant_id=os.environ["BRAINTREE_MERCHANT_ID"],
    public_key=os.environ["BRAINTREE_PUBLIC_KEY"],
    private_key=os.environ["BRAINTREE_PRIVATE_KEY"],
))


def show(label, result):
    if result.is_success:
        t = getattr(result, "transaction", None)
        print(f"OK   {label}: id={t.id} type={t.type} status={t.status} amount={t.amount}"
              f" instrument={t.payment_instrument_type}")
        return t
    errors = [f"{e.code} {e.message}" for e in result.errors.deep_errors] or [result.message]
    print(f"FAIL {label}: {'; '.join(errors)}")
    return None


# Braintree rejects an identical sale shortly after another one ("Gateway Rejected: duplicate", 23 Oct),
# so each run uses a slightly different amount.
cents = Decimal(random.randint(1, 99)) / 100
A = Decimal("40.00") + cents

# 1. Mocked PayPal payment, ~40
sale = show(f"sale {A} via mocked PayPal", gw.transaction.sale({
    "amount": str(A),
    "payment_method_nonce": "fake-paypal-one-time-nonce",
    "options": {"submit_for_settlement": True},
}))
if sale and sale.paypal_details:
    print(f"     paypal payer_email={sale.paypal_details.payer_email}")

# 2. Refunds. Mocked PayPal goes straight to "settling" and is refundable at once (first run, 23 Oct).
show("refund 25.00 (partial)", gw.transaction.refund(sale.id, "25.00"))
show("refund 25.00 again (25+25 > original)", gw.transaction.refund(sale.id, "25.00"))
show("refund 120.00 (> original)", gw.transaction.refund(sale.id, "120.00"))
show(f"refund {A - 25} (exactly the remainder)", gw.transaction.refund(sale.id, str(A - 25)))
show("refund 1.00 after fully refunded", gw.transaction.refund(sale.id, "1.00"))

# 4. Look the transaction up again
t = gw.transaction.find(sale.id)
print(f"FIND {t.id}: status={t.status} amount={t.amount} refund_ids={t.refund_ids}")

# 5. Vaulted PayPal (reorder / charge path, P7)
cust = gw.customer.create({"payment_method_nonce": "fake-paypal-billing-agreement-nonce"})
if cust.is_success:
    token = cust.customer.payment_methods[0].token
    print(f"OK   vault customer={cust.customer.id} method={type(cust.customer.payment_methods[0]).__name__}")
    show(f"charge {120 + cents} on vaulted PayPal", gw.transaction.sale({
        "amount": str(120 + cents), "payment_method_token": token,
        "options": {"submit_for_settlement": True}}))
    show(f"charge {1200 + cents} on vaulted PayPal (10x)", gw.transaction.sale({
        "amount": str(1200 + cents), "payment_method_token": token,
        "options": {"submit_for_settlement": True}}))
else:
    print(f"FAIL vault: {cust.message}")

# 6. Two separate orders for the same customer: can order B's transaction be refunded? (P2 is about ownership)
other = show(f"second sale {80 + cents} (another order)", gw.transaction.sale({
    "amount": str(80 + cents), "payment_method_nonce": "fake-paypal-one-time-nonce",
    "options": {"submit_for_settlement": True}}))
if other:
    show("refund 30.00 on the other order", gw.transaction.refund(other.id, "30.00"))
