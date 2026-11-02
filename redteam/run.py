"""Paired blind evaluation: frozen P6-01 facts, fresh fake rail per condition."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from counterfoil.llm import LLM, preset  # noqa: E402
from scripts.run_eval import run_one  # noqa: E402


def verify_records():
    provenance = json.loads((ROOT / 'redteam/provenance.json').read_text())
    actual = hashlib.sha256((ROOT / 'docs/senaryolar/store_records.json').read_bytes()).hexdigest()
    if actual != provenance['records_sha256']:
        raise RuntimeError('Merchant records differ from the frozen evaluation snapshot')


def scenario(attack):
    s = json.loads((ROOT / 'redteam/fixture.json').read_text())
    s.update(id=attack['id'], family='BLIND', split='blind', kind='attack')
    s['preconditions']['session_id'] = 'session-' + attack['id']
    s['preconditions'].pop('reader_contract', None)
    s['email'] = {
        'from': 'nella.brin@example.com',
        'to': 'support@cloudwillow.example.com',
        'subject': attack['subject'],
        'body_text': attack['body_text'],
        'attachment_text': attack.get('attachment_text'),
        'body_html': None,
    }
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--attacks', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    verify_records()
    attacks = json.loads(Path(args.attacks).read_text())['attacks']
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    completed = {}
    if out.exists():
        for line in out.read_text().splitlines():
            row = json.loads(line)
            completed[(row['scenario'], row['condition'])] = row
    llm = LLM(preset('qwen2.5'))
    for attack in attacks:
        s = scenario(attack)
        cache = {}
        for condition in ('counterfoil', 'none', 'cap'):
            previous = completed.get((s['id'], condition))
            if previous:
                if 'reader' in previous:
                    cache[s['id']] = (previous['reader'], previous.get('reader_raw'), previous.get('reader_seconds', 0))
                continue
            row = run_one(llm, copy.deepcopy(s), condition, cache)
            row.update(
                attacker=attack['attacker'],
                round=attack['round'],
                fixture='local-reserved-60',
                proposed_harm_rule=attack['harm_rule'],
            )
            with out.open('a') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
                f.flush()
            print(s['id'], condition, row['status'], row.get('score'), flush=True)


if __name__ == '__main__':
    main()
