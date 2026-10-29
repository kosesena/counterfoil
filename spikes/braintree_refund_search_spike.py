"""transaction.search for money that went back out (26 Oct).

Questions: does a search for credits find a refund made seconds ago (search index lag), does it carry the refunded
sale's id, does `refund == True` separate refunds from standalone credits (transaction.credit: money out with no sale
behind it), and how many credits does the sandbox account hold for one day?
"""
import os
import random
import time
from datetime import UTC, datetime, timedelta
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
S = braintree.TransactionSearch
start = datetime.now(UTC) - timedelta(minutes=1)

amount = Decimal("30.00") + Decimal(random.randint(1, 99)) / 100
sale = gw.transaction.sale({"amount": str(amount), "payment_method_nonce": "fake-paypal-one-time-nonce",
                            "options": {"submit_for_settlement": True}, **account}).transaction
refund = gw.transaction.refund(sale.id, "7.00").transaction
try:
    credit = gw.transaction.credit({"amount": "3.00", "payment_method_nonce": "fake-valid-nonce", **account})
    credit = credit.transaction if credit.is_success else print("credit refused:", credit.message)
except braintree.exceptions.AuthorizationError:
    credit = print("credit refused: AuthorizationError (standalone credits are off for this sandbox merchant)")
print(f"sale {sale.id}, refund {refund.id}, standalone credit {credit and credit.id}")

for wait in (0, 5, 10, 20, 40):
    time.sleep(wait)
    found = {t.id: t for t in gw.transaction.search(S.type == "credit", S.created_at >= start).items}
    print(f"after +{wait}s: {len(found)} credit(s) since start; refund found={refund.id in found}, "
          f"credit found={bool(credit) and credit.id in found}")
    if refund.id in found and (not credit or credit.id in found):
        break
for t in found.values():
    print(f"     {t.id}: type={t.type} amount={t.amount} status={t.status} "
          f"refunded_transaction_id={t.refunded_transaction_id}")
only = [t.id for t in gw.transaction.search(S.type == "credit", S.refund == True, S.created_at >= start).items]  # noqa: E712
print("refund == True:", only)
only = [t.id for t in gw.transaction.search(S.type == "credit", S.refund == False, S.created_at >= start).items]  # noqa: E712
print("refund == False:", only)
day = gw.transaction.search(S.type == "credit", S.created_at >= datetime.now(UTC) - timedelta(days=1))
print("credits in the last 24 h on this sandbox account:", day.maximum_size)
