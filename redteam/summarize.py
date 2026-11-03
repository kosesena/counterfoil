"""Rescore saved evidence and publish a reproducible, error-aware summary (no model calls)."""

import json
from collections import defaultdict

from redteam.oracle import judge
from redteam.run import ROOT, scenario


def collect():
    records = json.loads((ROOT / 'redteam/store_records.json').read_text())
    attacks = {}
    for path in (ROOT / 'redteam').glob('attacks-codex-r*.json'):
        for attack in json.loads(path.read_text())['attacks']:
            attacks[attack['id']] = attack
    rows = []
    for path in sorted((ROOT / 'results').glob('2026-11-02-blind-codex-*.jsonl')):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            s = scenario(attacks[row['scenario']])
            if row['fixture'] == 'hosted-no-reservation':
                s['preconditions']['active_reservations'] = []
            row['record_oracle'] = judge(row.get('steps', []), records, s['preconditions'])
            row['evidence_file'] = str(path.relative_to(ROOT))
            rows.append(row)
    return rows


def table(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['fixture'], row.get('model', 'unknown'), row['round'], row['condition'])].append(row)
    lines = [
        '| Fixture | Agent | Round | Condition | Runs | Errors | Unknown outcomes | Deviating call | Existing harm | Record harm |',
        '|---|---|---:|---|---:|---:|---:|---:|---:|---:|',
    ]
    for key, rs in sorted(groups.items()):
        good = [r for r in rs if r.get('status') == 'ok' and 'score' in r]
        vals = [
            len(rs),
            len(rs) - len(good),
            sum(r['record_oracle']['outcome_unknown'] or r.get('outcome_unknown', False) for r in rs),
            sum(r['score']['attempt'] for r in good),
            sum(r['score']['harm'] for r in good),
            sum(r['record_oracle']['harm'] for r in good),
        ]
        lines.append('| ' + ' | '.join(map(str, [*key, *vals])) + ' |')
    return '\n'.join(lines)


def main():
    rows = collect()
    (ROOT / 'redteam/scored.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n')
    result = table(rows)
    (ROOT / 'redteam/summary-table.md').write_text(result + '\n')
    print(result)


if __name__ == '__main__':
    main()
