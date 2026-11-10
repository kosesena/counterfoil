"""Re-run the finished families' attacks under Counterfoil only, after the void fix (PR #96).

Each case reuses the Reader hand-off saved in its earlier Counterfoil row, so the only change between the two runs
is the gate. The agent is the same local model, so its calls can still differ from the first run.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from counterfoil.llm import LLM, preset  # noqa: E402
from redteam.run import scenario, verify_records  # noqa: E402
from scripts.run_eval import run_one  # noqa: E402

FAMILIES = ('muse-spark', 'gpt-5.6', 'deepseek-v4.1', 'mistral-large')


def main() -> None:
    verify_records()
    llm = LLM(preset('qwen2.5'))
    for name in FAMILIES:
        before = {}
        for line in (ROOT / f'results/2026-11-09-multi-family-{name}.jsonl').read_text().splitlines():
            row = json.loads(line)
            if row['condition'] == 'counterfoil':
                before[row['scenario']] = row
        out = ROOT / f'results/2026-11-10-gate-fix-{name}.jsonl'
        done = {json.loads(line)['scenario'] for line in out.read_text().splitlines()} if out.exists() else set()
        for round_no in (1, 2, 3):
            path = ROOT / f'redteam/attacks-multi-family/{name}-r{round_no}.json'
            for attack in json.loads(path.read_text())['attacks']:
                s = scenario(attack)
                if s['id'] in done or s['id'] not in before:
                    continue
                old = before[s['id']]
                cache = {s['id']: (old['reader'], old.get('reader_raw'), old.get('reader_seconds', 0))}
                row = run_one(llm, copy.deepcopy(s), 'counterfoil', cache)
                row.update(
                    attacker=attack['attacker'],
                    round=attack['round'],
                    fixture='local-reserved-60',
                    goal=attack['goal'],
                    email=s['email'],
                    gate='after-void-fix',
                )
                with out.open('a') as f:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
                print(s['id'], row['status'], flush=True)


if __name__ == '__main__':
    main()
