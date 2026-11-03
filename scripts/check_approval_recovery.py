"""Exercise approval and restart safety with isolated fixtures; optionally use real Braintree sandbox calls.

python -m scripts.check_approval_recovery --rail fake --output /tmp/recovery.json
Use --rail braintree --env-file /path/to/.env for sandbox evidence. Faults are injected locally,
not provider outages. Restart means close/reopen the ledger and construct a fresh Gateway.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv

from counterfoil.gateway import APPROVAL, BLOCK, Gateway
from counterfoil.rail import FakeRail, SandboxRail
from counterfoil.scenarios import attempt, build, load_records, load_scenarios
from counterfoil.store import Store

CASES = (
    'approve',
    'reject',
    'expire',
    'pending-restart',
    'refund-timeout-before',
    'refund-timeout-after',
    'refund-crash-before',
    'refund-crash-after',
    'charge-timeout-before',
    'charge-timeout-after',
    'charge-crash-before',
    'charge-crash-after',
)


class InterruptedProcess(BaseException):
    """Bypass normal exception handling at the rail boundary, before outcome persistence."""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_case(name: str, rail_kind: str, db: str) -> dict:
    scenario = next(
        s for s in load_scenarios() if s['id'] == ('CLEAN-06' if name.startswith('charge-') else 'CLEAN-01')
    )
    fixture, _, ctx = build(scenario)
    fixture.db.close()
    store = Store(load_records(), db)
    rail = (
        SandboxRail(store, f'recovery-{uuid.uuid4().hex[:12]}')
        if rail_kind == 'braintree'
        else FakeRail.from_store(store)
    )
    now = datetime.now(UTC)
    gate = Gateway(store, rail, clock=lambda: now)
    tool, args = attempt(scenario)
    ctx.blocked_attempts = 1  # clean request held for manager review following a blocked attempt
    held = gate.handle(ctx, tool, args)
    require(held.decision == APPROVAL and not rail.money_calls(), 'request must wait for approval')
    result = {'case': name, 'heldBeforeMoney': True}
    try:
        if name == 'reject':
            require(gate.reject(held.approval_id), 'reject failed')
        elif name == 'expire':
            now += timedelta(minutes=31)
            expired = gate.approve(held.approval_id)
            require('APPROVAL_EXPIRED' in {f.code for f in expired.findings}, 'expired approval accepted')
        elif name == 'pending-restart':
            store.db.close()
            store = Store(load_records(), db)
            gate = Gateway(store, rail)
        elif name == 'approve':
            require(gate.approve(held.approval_id).executed, 'approved payment failed')
        else:
            original = getattr(rail, tool)
            accepted = False

            def fault(*a):
                nonlocal accepted
                if name.endswith('-after'):
                    require(original(*a).ok, 'sandbox operation failed before fault injection')
                    accepted = True
                if '-crash-' in name:
                    raise InterruptedProcess()
                raise TimeoutError('injected lost response')

            setattr(rail, tool, fault)
            try:
                first = gate.approve(held.approval_id)
                require(first.rail_state == 'unknown', 'timeout must remain unknown')
            except InterruptedProcess:
                require('-crash-' in name, 'unexpected interruption')
            finally:
                setattr(rail, tool, original)
            require(accepted == name.endswith('-after'), 'fault was not injected at the requested boundary')
            store.db.close()
            store = Store(load_records(), db)
            gate = Gateway(store, rail)
            retry = gate.handle(ctx, tool, args)
            require(retry.decision == BLOCK and not retry.reached_rail, 'restart retry reached payment rail')
            result['retryCodes'] = [f.code for f in retry.findings]
            result['ledgerState'] = store.sql(
                'SELECT status FROM charges' if tool == 'charge' else 'SELECT status FROM reservations'
            )
        replay = gate.approve(held.approval_id)
        require(replay.decision == BLOCK and not replay.reached_rail, 'approval replay reached rail')
        count = len(rail.money_calls())
        expected = 1 if name == 'approve' or name.endswith('-after') else 0
        require(count == expected, f'expected {expected} money calls, got {count}')
        if tool == 'refund':
            total = rail.refunded_total(store.orders[args['order_no']]['braintree_transaction_id'])
            require(total == (30 if expected else 0), 'provider refund total differs')
            result['providerRefundTotal'] = str(total)
        result.update(passed=True, moneyCalls=count, replayBlocked=True)
        return result
    finally:
        store.db.close()


def run(rail_kind: str) -> dict:
    with TemporaryDirectory(prefix='counterfoil-recovery-') as folder:
        cases = []
        for name in CASES:
            cases.append(run_case(name, rail_kind, str(Path(folder) / f'{name}.db')))
            print(f'{name}: PASS', flush=True)
    return {
        'recordedAt': datetime.now(UTC).isoformat(),
        'rail': rail_kind,
        'faults': 'locally injected',
        'restart': 'SQLite close/reopen and new Gateway; not a hosted process restart',
        'cases': cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rail', choices=['fake', 'braintree'], default='fake')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    if options.env_file:
        load_dotenv(options.env_file)
    result = run(options.rail)
    options.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
