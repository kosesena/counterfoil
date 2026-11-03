import json

import pytest

from scripts.export_recent_evidence import ROOT, cohort, export, normalise


def test_cohorts_keep_their_own_fixtures_and_denominators():
    data = {c['id']: c for c in export()['cohorts']}
    assert {k: c['runs'] for k, c in data.items()} == {
        'local-attacks': 90,
        'archived-pilot': 6,
        'hosted-attacks': 30,
        'clean-controls': 12,
        'clean-boundaries': 12,
        'remaining-clean': 12,
        'repeat-clean': 12,
    }
    local = {c['condition']: c for c in data['local-attacks']['conditions']}
    assert local['none']['recordHarm'] == 10 and local['none']['moneyHarm'] == 9
    assert local['counterfoil']['recordHarm'] == 0
    assert sum(c['unknown'] for c in data['archived-pilot']['conditions']) == 1
    assert data['archived-pilot']['status'] == 'incomplete'
    repeated = {c['condition']: c for c in data['repeat-clean']['conditions']}
    assert repeated['cap']['policyBypass'] == 2
    assert repeated['counterfoil']['reviewEligible'] == repeated['counterfoil']['explicitReview'] == 2


@pytest.mark.parametrize(('unknown', 'error'), [(True, False), (False, True), (True, True)])
def test_unknown_or_error_cannot_be_reported_as_completion(unknown, error):
    row = {
        'scenario': 'test',
        'condition': 'counterfoil',
        'status': 'error' if error else 'ok',
        'outcome_unknown': unknown,
        'score': {'legit_done': True},
        'record_oracle': {'harm': False, 'harm_reasons': [], 'outcome_unknown': False},
        'needs_human': True,
        'review_no_payment': True,
        'explicit_review': True,
    }
    result = normalise(row, clean=True)
    assert not result['completed'] and not result['reviewUnpaid'] and not result['explicitReview']


def test_duplicate_trial_is_rejected_instead_of_inflating_totals():
    row = {'scenario': 'test', 'condition': 'counterfoil'}
    with pytest.raises(ValueError, match='Duplicate'):
        cohort('test', 'test', '', '', [row, row])


def test_published_data_is_current_and_contains_only_scored_fields():
    expected = export()
    index = {**expected, 'cohorts': [{k: v for k, v in c.items() if k != 'scoredRuns'} for c in expected['cohorts']]}
    assert json.loads((ROOT / 'dashboard/public/recent-evidence.json').read_text()) == index
    for c in expected['cohorts']:
        published = json.loads((ROOT / 'dashboard/public' / c['download']).read_text())
        assert published == c
        assert all('reader' not in r and 'steps' not in r and 'hosted_raw' not in r for r in published['scoredRuns'])
