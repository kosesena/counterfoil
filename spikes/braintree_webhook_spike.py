"""A real chargeback in the Braintree sandbox, then a dispute webhook for it, then the next refund (29 Oct).

Real: the sale on the dispute test card, the chargeback Braintree opens on it, the settlement, the sandbox keys that
sign and verify the notification, and the refund attempt (nothing reaches Braintree if the gate blocks it).
Simulated: the delivery. The notification is the SDK's webhook_testing.sample_notification for the real transaction
id, signed with the real sandbox keys, handed to Counterfoil as Braintree would post it (directly, and through the
demo's /api/braintree/webhook). Braintree's own delivery needs a public URL set in the Control Panel; the sample
uses the transaction id as the dispute id too, so the dispute id it carries is not Braintree's.

To show the webhook's lock on its own, the gate's rail hides the disputes Braintree lists (as a rail that cannot
list them, or one that has not caught up, would). Before the webhook only `check` runs, so no refund can go out.
"""
import os
import random
import time
import urllib.parse
from decimal import Decimal

import braintree
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from counterfoil.gateway import Context, Gateway
from counterfoil.rail import BraintreeRail
from counterfoil.scenarios import load_records
from counterfoil.store import Store
from counterfoil.webhooks import Webhooks

load_dotenv()
assert os.environ["BRAINTREE_ENVIRONMENT"] == "sandbox"
rail = BraintreeRail()
gw = rail.gw
account = {"merchant_account_id": os.environ["BRAINTREE_MERCHANT_ACCOUNT_ID"]} if os.environ.get(
    "BRAINTREE_MERCHANT_ACCOUNT_ID") else {}


class NoDisputes:
    """The real sandbox rail, except that it lists no disputes."""

    def __getattr__(self, name):
        return getattr(rail, name)

    def disputes(self, transaction_id):
        return []


amount = Decimal("80.00") + Decimal(random.randint(1, 99)) / 100
r = gw.transaction.sale({"amount": str(amount), "credit_card": {"number": "4023898493988028", "expiration_date": "12/2030"},
                         "options": {"submit_for_settlement": True}, **account})
assert r.is_success, r.message
tid = r.transaction.id
print(f"REAL sale {tid} {amount} {r.transaction.currency_iso_code} on the dispute test card")
for _ in range(10):
    disputes = gw.transaction.find(tid).disputes
    if disputes:
        break
    time.sleep(3)
for d in disputes:
    print(f"REAL dispute {d.id}: {d.kind} {d.status} {d.amount_disputed} reason={d.reason}")
s = gw.testing.settle_transaction(tid)
print("REAL settle:", s.transaction.status if s.is_success else s.message)

records = load_records()
order = next(o for o in records["orders"] if o["order_no"] == "ST-1056")
order["braintree_transaction_id"] = tid  # the store's order is this real sale
order["total"] = str(amount)
store = Store(records)
gate = Gateway(store, NoDisputes())
args = {"order_no": "ST-1056", "rma_id": "RMA-1056", "amount": "40.00", "currency": order["currency"]}
reader = {"istek": "refund", "siparis_no": "ST-1056", "iade_kaydi_no": "RMA-1056", "tutar": "40.00",
          "para_birimi": order["currency"]}


def ctx():
    return Context("spike", order["customer_id"], frozenset({"refund"}), reader=dict(reader),
                   as_of=__import__("datetime").datetime.fromisoformat(order["created_at"].replace("Z", "+00:00")))


before = gate.check(ctx(), "refund", args)
print("before the webhook, check only:", [(f.severity, f.code) for f in before if f.severity != "PASS"] or "PASS")

n = gw.webhook_testing.sample_notification(braintree.WebhookNotification.Kind.DisputeOpened, tid)
got = Webhooks(store, gw).receive(n["bt_signature"], n["bt_payload"])
print(f"SIMULATED delivery, REAL keys: {got.kind} -> {got.action}; {got.detail['refunds_on_transaction']}")

out = gate.handle(ctx(), "refund", args)
print("next refund:", out.decision, out.rail_state, [f.code for f in out.findings if f.severity == "BLOCK"])
print("refunds Braintree holds on the sale:", list(gw.transaction.find(tid).refund_ids))
full = Gateway(store, rail).check(ctx(), "refund", args)
print("the gate on the unmodified rail:", [f.detail for f in full if f.code == "TRANSACTION_DISPUTED"])

# the same notification through the demo's endpoint, verified by the server's own keys
from demo.app import create_app  # noqa: E402
from demo.settings import Settings  # noqa: E402

c = TestClient(create_app(Settings.from_env()))
form = urllib.parse.urlencode({"bt_signature": n["bt_signature"], "bt_payload": n["bt_payload"].decode()})
hdr = {"content-type": "application/x-www-form-urlencoded"}
print("demo endpoint:", c.post("/api/braintree/webhook", content=form, headers=hdr).json())
print("demo endpoint, same again:", c.post("/api/braintree/webhook", content=form, headers=hdr).json())
bad = urllib.parse.urlencode({"bt_signature": n["bt_signature"], "bt_payload": n["bt_payload"].decode()[:-6] + "AAAA\n"})
print("demo endpoint, payload changed:", c.post("/api/braintree/webhook", content=bad, headers=hdr).status_code)
print("demo audit:", [(e["kind"], e["subject_id"], e["action"]) for e in c.get("/api/braintree/events").json()["events"]])
