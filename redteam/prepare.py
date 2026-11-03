"""Validate and normalize a raw attacker reply; never invent missing cases."""

import argparse
import json
from pathlib import Path


def normalize(text, attacker, round_no, count):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    data = json.loads(text)
    attacks = data['attacks']
    if len(attacks) != count:
        raise ValueError(f'Expected {count} attacks; received {len(attacks)}')
    ids = set()
    for a in attacks:
        if a['id'] in ids:
            raise ValueError('duplicate attack id')
        ids.add(a['id'])
        for field in ('subject', 'body_text', 'goal'):
            if not isinstance(a[field], str) or not a[field].strip():
                raise ValueError(f'invalid {field}')
        if len(a['subject']) > 300:
            raise ValueError('subject exceeds hosted limit')
        if not isinstance(a['harm_rule'], dict):
            raise ValueError('harm_rule must be an object')
        if a.get('attachment_text') is not None and not isinstance(a['attachment_text'], str):
            raise ValueError('invalid attachment_text')
        if len(a['subject']) + len(a['body_text']) + len(a.get('attachment_text') or '') > 4000:
            raise ValueError('email exceeds hosted limit')
        a.update(id=f'{attacker}-{a["id"]}', attacker=attacker, round=round_no)
    return {'attacks': attacks}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('raw')
    p.add_argument('out')
    p.add_argument('--attacker', required=True)
    p.add_argument('--round', type=int, required=True)
    p.add_argument('--count', type=int, required=True)
    a = p.parse_args()
    data = normalize(Path(a.raw).read_text(), a.attacker, a.round, a.count)
    Path(a.out).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print('validated', len(data['attacks']), 'attacks')


if __name__ == '__main__':
    main()
