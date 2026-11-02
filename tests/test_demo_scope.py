"""The demo wrapper preserves rail capabilities without widening the fixture scope."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from counterfoil.gateway import Gateway
from counterfoil.scenarios import attempt, build, load_scenarios
from demo.scope import ScopedRail


@pytest.fixture
def scene():
    scenario = next(s for s in load_scenarios() if s['id'] == 'CLEAN-01')
    store, inner, ctx = build(scenario)
    yield scenario, store, inner, ctx, ScopedRail(inner, store, 'fake')
    store.db.close()


def test_refund_request_key_preserves_idempotency(scene):
    _, store, inner, _, rail = scene
    txn = store.orders['ST-1042']['braintree_transaction_id']
    first = rail.refund(txn, Decimal('30.00'), 'same-refund')
    again = rail.refund(txn, Decimal('30.00'), 'same-refund')
    assert first.ok and again == first
    assert inner.txns[txn].refunded == Decimal('30.00')


def test_void_request_key_preserves_idempotency(scene):
    _, store, _, _, rail = scene
    txn = store.orders['ST-1058']['braintree_transaction_id']
    first = rail.void(txn, 'same-void')
    assert first.ok and rail.void(txn, 'same-void') == first


@pytest.mark.parametrize('method', ['refund', 'void', 'find', 'refunded_total', 'disputes', 'line_items'])
def test_foreign_transactions_never_reach_inner_rail(scene, method):
    _, _, inner, _, rail = scene
    args = (
        ('foreign-txn', Decimal('1.00'), 'key')
        if method == 'refund'
        else ('foreign-txn', 'key')
        if method == 'void'
        else ('foreign-txn',)
    )
    result = getattr(rail, method)(*args)
    assert (not result.ok) if method in ('refund', 'void') else result is None
    assert inner.calls == []


@pytest.mark.parametrize('method', ['disputes', 'line_items'])
def test_rails_without_optional_metadata_remain_supported(scene, method):
    _, store, _, _, _ = scene
    rail = ScopedRail(SimpleNamespace(), store, 'minimal')
    assert getattr(rail, method)(store.orders['ST-1042']['braintree_transaction_id']) is None


def test_gateway_still_sees_disputes_through_scope(scene):
    scenario, store, inner, ctx, rail = scene
    txn = store.orders['ST-1042']['braintree_transaction_id']
    inner.txns[txn].disputes = [{'id': 'dispute', 'status': 'open', 'kind': 'chargeback', 'amount': '90.00'}]
    result = Gateway(store, rail).handle(ctx, *attempt(scenario))
    assert result.decision == 'BLOCK'
    assert 'TRANSACTION_DISPUTED' in {f.code for f in result.findings}
    assert inner.money_calls() == []


def test_gateway_still_crosschecks_rail_line_items_through_scope(scene):
    scenario, store, inner, ctx, rail = scene
    txn = store.orders['ST-1042']['braintree_transaction_id']
    for line in inner.txns[txn].line_items:
        line['quantity'] = '0'
    result = Gateway(store, rail).handle(ctx, *attempt(scenario))
    assert result.decision == 'BLOCK'
    assert 'RAIL_ITEMS_MISMATCH' in {f.code for f in result.findings}
    assert inner.money_calls() == []
