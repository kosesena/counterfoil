"""Offline integrity checks for the completed, paired evaluation."""

import json
from collections import defaultdict

from redteam.run import ROOT, verify_records
from redteam.summarize import collect


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    verify_records()
    rows = collect()
    local = [r for r in rows if r['fixture'] == 'local-reserved-60']
    require(len(local) == 90, 'Expected 30 local cases × 3 conditions')
    groups = defaultdict(list)
    for r in local:
        groups[r['scenario']].append(r)
    require(len(groups) == 30, 'Expected exactly 30 unique local case IDs')
    for name, rs in groups.items():
        require(
            len(rs) == 3 and {r['condition'] for r in rs} == {'none', 'cap', 'counterfoil'},
            f'{name}: missing or duplicate condition',
        )
        require(all(r.get('reader') == rs[0].get('reader') for r in rs), f'{name}: unpaired Reader hand-off')
        require(all(r['rail'] == 'fake' for r in rs), f'{name}: unexpected rail')
    for rnd, count in ((1, 20), (2, 10)):
        attacks = json.loads((ROOT / f'redteam/attacks-codex-r{rnd}.json').read_text())['attacks']
        require(len(attacks) == count, f'Round {rnd}: wrong attack count')
        require(
            {a['id'] for a in attacks} == {r['scenario'] for r in local if r['round'] == rnd},
            f'Round {rnd}: case mismatch',
        )
        events = [
            json.loads(line) for line in (ROOT / f'redteam/raw/codex-r{rnd}.events.jsonl').read_text().splitlines()
        ]
        require(any(e['type'] == 'turn.completed' for e in events), f'Round {rnd}: attacker incomplete')
        require(
            all(e.get('item', {}).get('type', 'agent_message') == 'agent_message' for e in events),
            f'Round {rnd}: unexpected tool event',
        )
    feedback = json.loads((ROOT / 'redteam/feedback-codex-r1.json').read_text())
    require(len(feedback) == 20, 'Missing public feedback')
    require(all(set(f) == {'id', 'status', 'public_answers'} for f in feedback), 'Unexpected private feedback fields')
    for f in feedback:
        source = next(r for r in local if r['scenario'] == f['id'] and r['condition'] == 'counterfoil')
        expected = [
            {'decision': s['decision'], 'reason_codes': [x['code'] for x in s['findings'] if x['severity'] != 'PASS']}
            for s in source.get('steps', [])
        ]
        require(f['public_answers'] == expected, 'Feedback differs from public gate replies')
    hosted = [r for r in rows if r['fixture'] == 'hosted-no-reservation']
    require(len(hosted) == 6, 'Unexpected hosted pilot count')
    require(
        sum(r['record_oracle']['outcome_unknown'] for r in hosted) == 1, 'Hosted unknown outcome must remain visible'
    )
    print(
        'Integrity passed: 30 cases, 90 paired local rows, 6 hosted pilot rows, 1 hosted unknown; 0 attacker tool calls.'
    )


if __name__ == '__main__':
    main()
