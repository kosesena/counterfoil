"""Record harm per attacker family, before and after the void fix, from the saved rows (no model calls)."""

import json
from collections import Counter

from redteam.oracle import judge
from redteam.run import ROOT

FAMILIES = ('muse-spark', 'gpt-5.6', 'deepseek-v4.1', 'mistral-large')
CONDITIONS = ('none', 'cap', 'counterfoil')


def count(path, conditions=CONDITIONS):
    records = json.loads((ROOT / 'redteam/store_records.json').read_text())
    pre = json.loads((ROOT / 'redteam/fixture.json').read_text())['preconditions']
    c = Counter()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        cond = row['condition']
        if cond not in conditions:
            continue
        if row['status'] != 'ok':
            c[cond, 'error'] += 1
            continue
        c[cond, 'runs'] += 1
        c[cond, 'harm'] += judge(row.get('steps', []), records, pre)['harm']
        for step in row.get('steps', []):
            if step['tool'] == 'void':
                c[cond, 'void ' + step['decision']] += 1
    return c


def main():
    total, after = Counter(), Counter()
    print('| Attacker | No gate | $200 cap | Counterfoil | Counterfoil after the void fix |')
    print('|---|---|---|---|---|')
    for name in FAMILIES:
        c = count(ROOT / f'results/2026-11-09-multi-family-{name}.jsonl')
        a = count(ROOT / f'results/2026-11-10-gate-fix-{name}.jsonl', ('counterfoil',))
        total.update(c)
        after.update(a)
        cells = [f"{c[k, 'harm']}/{c[k, 'runs']}" for k in CONDITIONS]
        print(f"| {name} | {' | '.join(cells)} | {a['counterfoil', 'harm']}/{a['counterfoil', 'runs']} |")
    cells = [f"{total[k, 'harm']}/{total[k, 'runs']}" for k in CONDITIONS]
    print(f"| total | {' | '.join(cells)} | {after['counterfoil', 'harm']}/{after['counterfoil', 'runs']} |")
    print(
        'errors:',
        sum(v for k, v in total.items() if k[1] == 'error'),
        sum(v for k, v in after.items() if k[1] == 'error'),
    )
    print(
        'voids under Counterfoil before:',
        {k[1]: v for k, v in total.items() if k[0] == 'counterfoil' and 'void' in k[1]},
    )
    print('voids under Counterfoil after:', {k[1]: v for k, v in after.items() if 'void' in k[1]})


if __name__ == '__main__':
    main()
