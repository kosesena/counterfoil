"""Line items on a mocked-PayPal sale, read back with transaction_line_item.find_all (26 Oct).

Question: does the sandbox keep the line items we send on a mocked-PayPal sale, and does find_all return them with
the quantities and amounts the gate compares (product_code, quantity, unit_amount, total_amount)?
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

cents = Decimal(random.randint(1, 99)) / 100  # avoid the 30-second duplicate check
lines = [
    {"kind": "debit", "name": "Willowfold tote", "product_code": "BAG", "quantity": "2",
     "unit_amount": "40.00", "total_amount": "80.00"},
    {"kind": "debit", "name": "Spike line", "product_code": "SPIKE", "quantity": "1",
     "unit_amount": str(cents), "total_amount": str(cents)},
]
sale = {"amount": str(Decimal("80.00") + cents), "payment_method_nonce": "fake-paypal-one-time-nonce",
        "order_id": "spike-line-items", "line_items": lines, "options": {"submit_for_settlement": True}}
if os.environ.get("BRAINTREE_MERCHANT_ACCOUNT_ID"):
    sale["merchant_account_id"] = os.environ["BRAINTREE_MERCHANT_ACCOUNT_ID"]
r = gw.transaction.sale(sale)
assert r.is_success, r.message
t = r.transaction
print(f"OK   sale id={t.id} amount={t.amount} instrument={t.payment_instrument_type} status={t.status}")
for li in gw.transaction_line_item.find_all(t.id):
    print(f"     line {li.product_code}: quantity={li.quantity!r} unit_amount={li.unit_amount!r} "
          f"total_amount={li.total_amount!r} kind={li.kind} name={li.name!r}")
refund = gw.transaction.refund(t.id, "10.00")
print("     refund before settlement:", "OK" if refund.is_success else "; ".join(
    f"{e.code} {e.message}" for e in refund.errors.deep_errors) or refund.message)
if refund.is_success:
    print(f"     line items on the refund {refund.transaction.id}: {gw.transaction_line_item.find_all(refund.transaction.id)}")
try:
    gw.transaction_line_item.find_all("does-not-exist")
except braintree.exceptions.NotFoundError:
    print("     find_all on an unknown id: NotFoundError")
