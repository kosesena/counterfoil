"""Same over-refund probe as braintree_spike.py, but with a test card instead of mocked PayPal.

Question: is "refund > original amount accepted" (seen with mocked PayPal, 23 Oct) a property of
mocked PayPal, or of the sandbox in general?
"""
import os
import random
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


def show(label, result):
    if result.is_success:
        t = getattr(result, "transaction", None)
        print(f"OK   {label}: id={t.id} type={t.type} status={t.status} amount={t.amount}")
        return t
    errors = [f"{e.code} {e.message}" for e in result.errors.deep_errors] or [result.message]
    print(f"FAIL {label}: {'; '.join(errors)}")
    return None


A = Decimal("40.00") + Decimal(random.randint(1, 99)) / 100
sale = show(f"card sale {A}", gw.transaction.sale({
    "amount": str(A), "payment_method_nonce": "fake-valid-nonce",
    "options": {"submit_for_settlement": True}}))
show("refund 10.00 before settlement", gw.transaction.refund(sale.id, "10.00"))
show("testing.settle_transaction", gw.testing.settle_transaction(sale.id))
show("refund 25.00", gw.transaction.refund(sale.id, "25.00"))
show("refund 25.00 again (total > original)", gw.transaction.refund(sale.id, "25.00"))
show("refund 120.00 (> original)", gw.transaction.refund(sale.id, "120.00"))
show(f"refund {A - 25} (remainder)", gw.transaction.refund(sale.id, str(A - 25)))
show("refund 1.00 after fully refunded", gw.transaction.refund(sale.id, "1.00"))
