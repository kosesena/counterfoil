import pytest

from counterfoil.gateway import Gateway
from counterfoil.scenarios import attempt, build
from redteam.clean_boundaries import evaluate, load

SCENARIOS = load()[1]


@pytest.mark.parametrize('scenario', SCENARIOS, ids=lambda s: s['id'])
def test_boundary_preconditions_produce_expected_decision(scenario):
    store, rail, ctx = build(scenario)
    result = Gateway(store, rail).handle(ctx, *attempt(scenario))
    assert result.decision == scenario['expected_gateway_decision']
    assert result.rail_state == ('succeeded' if result.decision == 'PASS' else 'not_called')
    store.db.close()


def row(scenario, decision, state):
    tool, args = attempt(scenario)
    return {'steps': [{'tool': tool, 'args': args, 'decision': decision, 'rail_state': state, 'findings': []}]}


@pytest.mark.parametrize('scenario', SCENARIOS[2:], ids=lambda s: s['id'])
def test_staff_review_distinguishes_approval_abstention_and_bypass(scenario):
    held = evaluate(row(scenario, 'APPROVAL', 'not_called'), scenario)
    assert held['explicit_review'] and held['review_no_payment']
    assert not held['valid_auto_refund_held']
    abstention = evaluate({'steps': []}, scenario)
    assert abstention['review_no_payment'] and not abstention['explicit_review']
    paid = evaluate(row(scenario, 'PASS', 'succeeded'), scenario)
    assert paid['score']['policy_bypass'] and paid['record_oracle']['harm']
    assert not paid['review_no_payment']


def test_unknown_cannot_count_as_completed_or_safe():
    for scenario in SCENARIOS:
        result = evaluate(row(scenario, 'PASS', 'unknown'), scenario)
        assert result['outcome_unknown']
        assert not result['auto_completed'] and not result['review_no_payment']
