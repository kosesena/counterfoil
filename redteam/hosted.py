"""Small hosted subset; honor Retry-After and preserve raw replies, no retries on ambiguous POST failures."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from counterfoil.evaluate import expected_outcome, score  # noqa: E402
from counterfoil.scenarios import build  # noqa: E402
from redteam.run import scenario, verify_records  # noqa: E402

URL = 'https://counterfoil-demo.onrender.com/api/run'


def uncertain(row):
    return bool(row.get('outcome_unknown')) or any(s.get('rail_state') == 'unknown' for s in row.get('steps', []))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--attacks', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()
    verify_records()
    attacks = json.loads(Path(args.attacks).read_text())['attacks'][: args.limit]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if out.exists():
        done = {(r['scenario'], r['condition']): r for r in map(json.loads, out.read_text().splitlines())}
        if any(uncertain(r) for r in done.values()):
            raise SystemExit('Prior run has an uncertain outcome; resolve it before resuming.')
    for a in attacks:
        s = scenario(a)
        s['preconditions']['active_reservations'] = []
        s['ground_truth']['correct_amount'] = '100.00'
        store, _, _ = build(s)
        handoff = None
        for cond in ('counterfoil', 'none', 'cap'):
            if (a['id'], cond) in done:
                handoff = done[(a['id'], cond)].get('reader')
                continue
            email = {k: v for k, v in s['email'].items() if k != 'to'}
            payload = json.dumps({'mode': 'live', 'condition': cond, 'email': email}).encode()
            while True:
                try:
                    req = urllib.request.Request(URL, data=payload, headers={'Content-Type': 'application/json'})
                    with urllib.request.urlopen(req, timeout=360) as response:  # noqa: S310 - fixed HTTPS sandbox URL
                        row = json.load(response)
                    break
                except urllib.error.HTTPError as exc:
                    body = exc.read().decode()
                    if exc.code == 429 and 'Retry-After' in exc.headers:
                        delay = max(1, int(exc.headers['Retry-After']))
                        print('rate-limit; waiting', delay, flush=True)
                        time.sleep(delay)
                        continue
                    row = {'status': 'http_error', 'http_status': exc.code, 'error': body}
                    break
                except (OSError, ValueError) as exc:
                    row = {'status': 'transport_error', 'error': str(exc), 'outcome_unknown': True}
                    break
            raw = row.copy()
            row.update(
                scenario=a['id'],
                condition=cond,
                attacker=a['attacker'],
                round=a['round'],
                fixture='hosted-no-reservation',
                hosted_raw=raw,
            )
            if 'steps' in row:
                row['score'] = score(row['steps'], expected_outcome(s, store), store).as_dict()
            if handoff is None:
                handoff = row.get('reader')
            row['paired_reader_matches'] = row.get('reader') == handoff
            with out.open('a') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
            print(a['id'], cond, row.get('status'), row.get('score'), flush=True)
            if row.get('status') in ('http_error', 'transport_error') or uncertain(row):
                return  # preserve uncertainty; no automatic repeat of a money-moving request


if __name__ == '__main__':
    main()
