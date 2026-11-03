import pytest

from redteam.repeat_clean import validate


def cohort():
    manifest = {'repeats': 2, 'conditions': ['counterfoil', 'none', 'cap']}
    scenarios = [{'id': 'CLEAN-01'}, {'id': 'CLEAN-06'}]
    rows = [
        {'trial': t, 'scenario': s['id'], 'condition': c, 'reader': {'case': s['id']}, 'paired_reader_matches': True}
        for t in (1, 2)
        for s in scenarios
        for c in manifest['conditions']
    ]
    return rows, manifest, scenarios


def test_trial_ids_prevent_silent_deduplication_or_replacement():
    rows, manifest, scenarios = cohort()
    assert validate(rows, manifest, scenarios)
    rows[-1] = rows[0].copy()
    with pytest.raises(ValueError, match='Missing or duplicate'):
        validate(rows, manifest, scenarios)


def test_mismatched_condition_reader_invalidates_pairing():
    rows, manifest, scenarios = cohort()
    rows[0]['reader'] = {'different': True}
    with pytest.raises(ValueError, match='Unpaired Reader'):
        validate(rows, manifest, scenarios)


def test_changed_reader_between_trials_is_reported_not_hidden():
    rows, manifest, scenarios = cohort()
    for r in rows:
        if r['trial'] == 2:
            r['reader'] = {'changed': r['scenario']}
    assert not validate(rows, manifest, scenarios)
