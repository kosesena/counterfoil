import pytest

from counterfoil.gateway import Gateway
from counterfoil.scenarios import attempt, build
from redteam.clean_boundaries import evaluate, load
from redteam.remaining_clean import MANIFEST

SCENARIOS = load(MANIFEST)[1]


@pytest.mark.parametrize('scenario', SCENARIOS, ids=lambda s: s['id'])
def test_remaining_clean_fixture_decisions(scenario):
    store, rail, ctx = build(scenario)
    result = Gateway(store, rail).handle(ctx, *attempt(scenario))
    assert result.decision == scenario['expected_gateway_decision']
    assert result.rail_state == ('succeeded' if result.decision == 'PASS' else 'not_called')
    store.db.close()


def test_paid_reorder_is_policy_bypass_even_at_correct_amount():
    scenario = SCENARIOS[-1]
    tool, args = attempt(scenario)
    step = {'tool': tool, 'args': args, 'decision': 'PASS', 'rail_state': 'succeeded', 'findings': []}
    result = evaluate({'steps': [step]}, scenario)
    assert result['score']['policy_bypass'] and result['record_oracle']['harm']
    assert not result['review_no_payment'] and not result['auto_completed']
    step.update(decision='APPROVAL', rail_state='not_called')
    held = evaluate({'steps': [step]}, scenario)
    assert held['explicit_review'] and held['review_no_payment']


def test_verified_failed_refund_does_not_consume_entitlement():
    scenario = next(s for s in SCENARIOS if s['id'] == 'CLEAN-05')
    assert scenario['preconditions']['required_refund_records'][0]['status'] == 'failed'
    tool, args = attempt(scenario)
    result = evaluate(
        {'steps': [{'tool': tool, 'args': args, 'decision': 'PASS', 'rail_state': 'succeeded', 'findings': []}]},
        scenario,
    )
    assert result['auto_completed'] and not result['record_oracle']['harm']
