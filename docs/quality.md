# Quality: how the gate is tested, and how well

Tests and coverage remeasured on 3 Nov 2026 (Python 3.14.5, macOS); CI uses Python 3.13. Mutation results below
are the historical 24 Oct measurement, not a new mutation run. Reproduction commands are under each heading.

| Measure | Number |
|---|---|
| Tests | **522** collected: **519 passed**, 2 skipped, 1 expected failure (P1-02 scoring, explained in the test) |
| Line + branch coverage, whole package | **94.74 %** |
| Line + branch coverage, `counterfoil/gateway.py` | **99 %** (2 defensive lines) |
| Mutation score, `counterfoil/gateway.py` | **94.8 %**, historical 24 Oct run (1217 of 1284 mutants killed; the 67 survivors are explained below) |
| Property tests | 8 hypothesis tests: a stateful model of the gate with 7 invariants, money parsing, and two fuzzers |
| Static checks | ruff (pyflakes, pycodestyle, isort, bugbear, pyupgrade, simplify, bandit), ruff format, mypy (`check_untyped_defs`) |
| Supply chain | pip-audit runs in PR CI; CodeQL `security-extended` is configured but was skipped on the recent PR runs, so it is not a completed scan claim |

CI (`.github/workflows/tests.yml`) runs the lint, type, test and audit jobs on every pull request and fails if
coverage drops below 90 %.

The November control/repeat cohorts and the dashboard export have offline integrity tests. The export checks
separate denominators, preserves the archived pilot's unknown outcome, excludes errors/unknowns from successful
completion, and compares published JSON with recomputed scores. Local Python 3.14 emitted SQLite ResourceWarnings
in the wider suite; those warnings did not fail the run. No live model or payment is needed to reproduce CI tests.

Dashboard validation: `cd dashboard && npm ci && npm run build` checks TypeScript and produces the static site.
`python -m scripts.export_recent_evidence` rebuilds the separate November evidence files without changing the
historical multi-model dataset. See [dashboard/README.md](../dashboard/README.md) for the two export paths.

## Set up

```bash
python3.13 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

## Tests and coverage

```bash
.venv/bin/pytest -q --cov --cov-report=term
```

The suite needs no network, no keys and no model: the rail is `FakeRail` (the card limits observed in the Braintree
sandbox) or, for the adapter tests, a stand-in for the `braintree` SDK; the agents run on scripted LLMs.

| File | What it pins down |
|---|---|
| `tests/test_scenarios.py` | Every scenario in `docs/senaryolar/scenarios.json` gets the expected decision and reason; no attack moves money through Counterfoil. |
| `tests/test_gateway_mechanics.py` | Approvals (single use, expiry, binding), reservations, concurrency, restart, reconciliation, parsing. Several tests reproduce code-review findings. |
| `tests/test_gateway_rules.py` | Every finding code with its severity and the smallest call that triggers it; boundaries (approval TTL, refund window, auto-refund limit); execution paths (void, charge claim, failed and unknown rail outcomes); the audit log. Written to close the gaps mutation testing found. |
| `tests/test_gateway_properties.py` | The invariants below, over generated call sequences. |
| `tests/test_rail_adapters.py` | `BraintreeRail` and `SandboxRail` against a fake SDK (sandbox-only guard, error codes, refund totals that ignore failed refunds, fixture-to-sandbox mapping); the run record never contains a key. |
| `tests/test_evaluate.py`, `test_agent_loop.py`, `test_llm_presets.py`, `test_demo.py` | Scoring, the agent loop, model presets, the live demo's limits and redaction. |

## Property-based tests

`tests/test_gateway_properties.py` uses [hypothesis](https://hypothesis.readthedocs.io). A rule-based state machine
plays several e-mail sessions from different customers (and one with no verified sender) against one store and rail.
Each step is one of: a refund (arbitrary or genuine), a charge (arbitrary or a genuine reorder, sometimes with an
inflated quantity the Reader did not see), a void, a lookup, a manager approving a held call (sometimes after the
stored arguments were tampered with), a manager rejecting one, the clock moving past the 30-minute approval window,
or the rail raising before or after it acted (a timeout). After every step:

1. **A BLOCKed or held call never reaches the rail**, and a call reaches it at most once, with exactly the arguments
   the gate checked.
2. **An approval executes at most once**, never after it expired, never after tampering, and only with the arguments
   it was issued for.
3. **Refunds per return record never exceed its approved amount** (accepted, completed and unknown refunds counted),
   unless a manager explicitly approved an `RMA_AMOUNT_MISMATCH` on it.
4. **Every refund the rail executed is in the store's ledger**: no money moves unrecorded, including when the rail
   acts and then times out.
5. **A call that executes without a human owns what it touches** (order, payment method), a lookup only returns the
   sender's own order, and **no charge executes without a human** (`CHARGE_NEEDS_CONFIRMATION`).
6. **One charge per e-mail reaches the rail**, approvals included.
7. **Amounts are exact**: every amount in the ledger is a `Decimal` with two places; `parse_amount` accepts only
   positive two-place values up to the maximum, never a float, and sums of parsed amounts equal the exact cent sums.

Every finding the gate returns also has a severity, an upper-case code and a non-empty explanation.

Two fuzzers feed malformed arguments: arbitrary JSON-like values for every argument, and a valid call with one
argument replaced. The gate must answer PASS, APPROVAL or BLOCK and never raise.

```bash
.venv/bin/pytest -q tests/test_gateway_properties.py                       # CI profile, about 4 s
HYPOTHESIS_PROFILE=thorough .venv/bin/pytest -q tests/test_gateway_properties.py   # 2000 runs × 60 steps, about 2 min
```

**What the property tests found.** A refund whose `rma_id` was a list or an object (an LLM can emit that) raised
`sqlite3.ProgrammingError` out of `Gateway.handle` instead of returning a decision. No money moved, but the agent run
crashed. It now returns BLOCK `RMA_UNKNOWN`. The invariants above held in every run, including the thorough profile.

## Mutation testing

[mutmut](https://mutmut.readthedocs.io) changes `counterfoil/gateway.py` one small edit at a time (a `>` becomes
`>=`, a constant becomes `None`, a `continue` becomes `break`, a string changes) and runs the tests against each
mutant. A mutant the tests do not notice ("survived") marks behaviour no test pins down.

```bash
HYPOTHESIS_PROFILE=mutation .venv/bin/mutmut run --max-children 8   # about 2 min on 8 cores
.venv/bin/mutmut results                                            # survivors; `mutmut show <name>` for a diff
```

The `mutation` hypothesis profile is derandomised, so a mutant is never killed or spared by luck.

| Run | Killed | Survived | Score |
|---|---|---|---|
| Before (existing tests + property tests) | 962 | 295 (+ 8 not covered) | 76.0 % |
| After `tests/test_gateway_rules.py` and the finding-shape invariant (gate incl. `CHARGE_NEEDS_CONFIRMATION`, 1284 mutants) | 1217 | 67 | 94.8 % |

The first run's survivors showed real gaps, now closed by tests:

- a successful `void` was never executed in any test (the gate's `void` rule could be deleted unnoticed);
- the boundaries of the approval window, the refund window and the auto-refund limit (`>` vs `>=`) were not pinned;
- a failed rail refund could have been recorded as *unknown* (blocking every later refund on the order) without a
  test failing;
- the Reader comparison of order number and currency, quantities named `qty` by the Reader or `adet` by the agent,
  and repeated SKU lines were untested;
- the charge claim being written *before* the rail is called (crash safety) was untested;
- several finding codes and severities, the blocked-attempt counter and the audit log entries were unchecked;
- an approval held after an earlier partial refund on the same return record was untested (the state the manager saw
  must include it).

The remaining survivors are equivalent or unreachable mutants, each looked at by hand:

- explanation texts of findings changed in wording or case (about half of them); the codes and severities are tested;
- the approval fingerprint's internal key names and `sort_keys` (the fingerprint is compared only with itself);
- default values that produce another non-existent order or token (`""` vs `None` vs `"XXXX"`);
- `fromisoformat` with or without the `Z` replacement (Python 3.11+ reads both);
- the Reader comparison's `continue` for an empty Reader field, which only optional fields can reach and the one
  optional field has its own branch;
- the reservation id length and an empty-string vs `None` sentinel.
