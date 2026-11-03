# Human approval and interrupted-payment validation · 3 November 2026

This protocol checks clean requests held for manager review, then injects failures before or after the payment
provider accepts the call. It does not use an LLM or adversarial email. Each case has its own sandbox fixture and
SQLite file. Results: `results/2026-11-03-approval-recovery.json`.

## Recorded result

All **12/12** Braintree sandbox cases passed on 3 November 2026. The HTTP and offline protocol subset passed
**58 tests**. The full suite passed **533 tests**, with 2 skipped and 1 expected failure; coverage remained **94.74%**.
No payment-gateway behavior change was necessary for these cases. Ruff and mypy passed.

## Protocol and expected outcomes

| Case | Expected payment calls | Expected subsequent behavior |
| --- | ---: | --- |
| Approve a held USD 30 refund | 1 | Reusing the approval is blocked |
| Reject the refund | 0 | Reusing the approval is blocked |
| Approve after 31 minutes | 0 | Expired approval is refused |
| Reopen ledger before deciding | 0 | Old approval is unknown; a new review is required |
| Refund timeout before / after acceptance | 0 / 1 | Unknown outcome survives reopening; retry is blocked |
| Refund interruption before / after acceptance | 0 / 1 | Reservation survives reopening; retry is blocked |
| Charge timeout before / after acceptance | 0 / 1 | Unknown charge survives reopening; retry is blocked |
| Charge interruption before / after acceptance | 0 / 1 | Requested charge survives reopening; retry is blocked |

The 12-case protocol runs against both FakeRail in CI and Braintree sandbox explicitly. A successful provider
response is required before an after-acceptance fault is injected. Refund totals are read back from the provider.
Setup sales and vaulted sandbox payment methods are excluded from the payment-call counts. Charges use the same
verified incoming request identity on retry. No customer funds or production payment endpoint is involved.

The HTTP integration suite separately exercises buy → held refund → approve/reject, duplicate decisions,
purchase binding, input validation, expiry and application recreation with the same simulated provider state.
These HTTP tests use a simulated Braintree SDK, not hosted browser interactions.

## What restart means here

The ledger is closed and reopened and a fresh Gateway is constructed. The payment provider and fixture-to-provider
mapping remain available. A BaseException at the call boundary represents an interruption before the gateway can
persist the outcome. This is controlled fault injection, not an actual provider outage, operating-system kill,
power-loss durability test or hosted deployment restart.

Unknown outcomes are deliberately held for reconciliation; the protocol proves duplicate prevention, not automatic
recovery or exactly-once delivery. An interruption before sending may leave an unused reservation or requested
charge. Do not release it merely because a timeout elapsed: first establish the provider outcome. Approval state is
in memory and is not restored. A new approval must recheck the current ledger and provider state.

The hosted demo also keeps purchases, held runs and per-run ledgers in memory. After restart, old purchase and
approval IDs fail closed; checkout cannot transparently resume. `DEMO_EVENTS_DB` persists webhook events/disputes
only, not checkout sessions or payment ledgers. A production integration needs a persistent payment ledger,
durable request identity and a reconciled recovery workflow. These checks do not establish that deployment setup.

## Reproduce

```sh
python -m pytest tests/test_approval_recovery.py tests/test_demo.py -q
python -m scripts.check_approval_recovery --rail fake --output /tmp/approval-recovery.json
# Creates isolated Braintree sandbox sales/refunds/charges; requires sandbox credentials.
python -m scripts.check_approval_recovery --rail braintree --env-file /path/to/.env \
  --output /tmp/approval-recovery-sandbox.json
```

The recorded artifact contains outcome counts, decision codes and ledger states, without credentials or provider IDs.
These operational checks are separate from the adversarial and clean-control model cohorts; do not pool their rates.
