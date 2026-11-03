"""The demo's "What if" rules. A relaxed gate drops exactly the findings behind the rules switched off; the checks
overlap, so no attack in the set gets through with any combination of them off (2 Nov: found while building it)."""

import itertools

import pytest

from counterfoil.gateway import APPROVAL, BLOCK, PASS, RELAXABLE, Gateway
from counterfoil.scenarios import attempt, build, load_scenarios

SCENARIOS = load_scenarios()
BY_ID = {s["id"]: s for s in SCENARIOS}


def run(scenario, relaxed=frozenset(), policy=None):
    store, rail, ctx = build(scenario)
    if policy:
        store.policy = {**store.policy, **policy}
    tool, args = attempt(scenario)
    return Gateway(store, rail, relaxed=frozenset(relaxed)).handle(ctx, tool, args)


def test_default_gate_is_unchanged():
    assert run(BY_ID["P6-01"]).decision == BLOCK


def test_a_relaxed_rule_drops_only_its_own_findings():
    out = run(BY_ID["P6-01"], {"return_record"})
    assert not {f.code for f in out.findings} & RELAXABLE["return_record"]
    # the reservation ledger at execution time still holds the second USD 60
    assert out.decision == BLOCK and {f.code for f in out.findings} == {"CONCURRENT_REFUND"}


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s["kind"] == "attack"], ids=lambda s: s["id"])
def test_no_combination_of_relaxed_rules_lets_an_attack_through(scenario):
    for k in range(len(RELAXABLE) + 1):
        for combo in itertools.combinations(RELAXABLE, k):
            assert run(scenario, combo).decision != PASS, combo


def test_another_customers_order_stays_held_whatever_is_relaxed():
    assert run(BY_ID["P2-01"], RELAXABLE).decision == APPROVAL


def test_the_auto_refund_limit_is_the_stores_choice():
    # the genuine USD 300 return waits for a person under the USD 200 limit and passes under a USD 400 one
    assert run(BY_ID["CLEAN-07"]).decision == APPROVAL
    assert run(BY_ID["CLEAN-07"], policy={"auto_refund_limit": "400.00"}).decision == PASS


def test_unknown_rule_is_refused():
    store, rail, _ = build(BY_ID["P6-01"])
    with pytest.raises(ValueError):
        Gateway(store, rail, relaxed=frozenset({"everything"}))
