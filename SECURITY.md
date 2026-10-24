# Security policy

## Scope

Counterfoil is a hackathon research prototype. It only ever talks to the **Braintree sandbox**:
`BraintreeRail` refuses to start unless `BRAINTREE_ENVIRONMENT=sandbox` (`counterfoil/rail.py`), and no production
keys exist for this project. No real money and no real customer data are involved; the store, customers, orders and
payment methods are fixtures in `docs/senaryolar/store_records.json`.

In scope:

- the gate (`counterfoil/gateway.py`) and its store and rail adapters: any sequence of tool calls that moves sandbox
  money the store's own records do not allow, reads another customer's data, or executes a held call without the
  approval it was bound to;
- the live demo (`demo/`): leaking the sandbox keys or the model API key, bypassing the rate limits or the daily budget,
  or making the demo's rail touch anything outside the fixture store.

Out of scope: the Blender scenes (`tools/`), throwaway experiments (`spikes/`), findings that need a compromised host or
a malicious repository maintainer, and attacks on Braintree, PayPal or the model providers themselves.

What the gate deliberately does *not* stop is written down in [`docs/threat-model.md`](docs/threat-model.md). A call the
records allow passes by design, so "the gate let a refund within an open return record through" is not a vulnerability
unless the record itself was wrong.

## Supported versions

Only the `main` branch is maintained.

## Reporting a vulnerability

Please report privately through GitHub: **Security → Report a vulnerability** on this repository (private
vulnerability reporting). If that is not available to you, open an issue that says only that you have a security
report, without details, and you will be given a private channel.

Please include the scenario or the exact tool-call sequence, what you expected the gate to decide, and what it did.
A failing pytest case is the most useful form. You can expect an acknowledgement within a few days; fixes land on
`main` with a regression test.

## What the repository does to stay safe

- CI on every pull request: ruff (including the bandit `S` rules), mypy, the test suite with a coverage floor, and
  `pip-audit` against the PyPI advisory database (`.github/workflows/tests.yml`).
- CodeQL code scanning with the `security-extended` queries (`.github/workflows/codeql.yml`).
- Secrets live only in the environment (`.env`, never committed; `.env.example` lists the names). The demo redacts the
  key values from every response it returns.
