'use client';

// "Why held, why blocked": an AG Studio custom widget that shows one held or blocked call at a time, as a
// case file the case agent (./case-agent.ts) builds from the store record. The widget lists the calls
// through its widgetApi, so the page's condition and decision buttons choose which calls it steps through. It only shows; approving is the merchant's
// job on the live demo.

import { useEffect, useState, useSyncExternalStore } from 'react';
import type { AgWidgetData, AgWidgetDataFormat, AgWidgetFieldReference, AgWidgetParams } from 'ag-studio';
import type { AgWidgetDefinition } from 'ag-studio-react';
import { caseStore, requestCase, type CaseFile } from './case-agent';

type Mapping = { callKey: AgWidgetFieldReference[] };
type CaseWidget = AgWidgetData<Mapping, AgWidgetDataFormat<unknown>>;

const DEMO = 'https://counterfoil-demo.onrender.com';
const usd = (v: number | null) => (v === null ? '—' : `$${v.toFixed(2)}`);

// The held and blocked call ids the page's filters leave, refetched when a filter changes.
function useCallIds(params: AgWidgetParams<CaseWidget>) {
  const { widgetApi, dataMapping } = params;
  const [ids, setIds] = useState<string[] | null>(null);
  const field = dataMapping.callKey?.[0];
  useEffect(() => {
    if (!field) return;
    let live = true;
    widgetApi
      .getData({ fields: [field], sort: [{ field, direction: 'asc' }] })
      .then((r) => live && setIds(r.results.rows.map((row) => String(row[field.key]))))
      .catch(() => live && setIds([]));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [widgetApi, field?.key, params]);
  return ids;
}

function Amounts({ file }: { file: CaseFile }) {
  const over = file.allows !== null && file.asked !== null && file.asked > file.allows + 0.005;
  const cells = [
    { label: 'Store record allows', value: file.allows, note: file.tool === 'charge' ? 'catalog price × Reader items' : `left on ${file.rmaId ?? 'the RMA'}` },
    { label: 'Reader handed off', value: file.handedOff, note: file.handedOff === null ? 'no amount in the hand-off' : 'from the e-mail, no tools' },
    { label: 'Agent asked', value: file.asked, note: over ? `${usd(file.asked! - file.allows!)} over the record` : 'within the record' },
  ];
  return (
    <div className="case-amounts">
      {cells.map((c, i) => (
        <div key={c.label} className={i === 2 ? (over ? 'over' : 'within') : ''}>
          <small>{c.label}</small>
          <strong>{usd(c.value)}</strong>
          <span>{c.note}</span>
        </div>
      ))}
    </div>
  );
}

function Ledger({ file }: { file: CaseFile }) {
  if (file.tool !== 'refund') return null;
  return (
    <div className="case-ledger">
      <small>Refunds already on {file.orderNo}</small>
      <ol>
        {file.ledger.length === 0 && <li className="none">None before this call</li>}
        {file.ledger.map((l, i) => (
          <li key={i}>
            <span>{l.source}</span>
            <span>{l.rmaId ?? 'no RMA'}</span>
            <span>{l.status}</span>
            <b>{usd(l.amount)}</b>
          </li>
        ))}
        <li className="this">
          <span>This request</span>
          <span>{file.rmaId ?? 'no RMA'}</span>
          <span>{file.decision === 'BLOCK' ? 'blocked' : 'held'}</span>
          <b>{usd(file.asked)}</b>
        </li>
      </ol>
      {file.approved !== null && (
        <p>
          {file.rmaId} approves {usd(file.approved)} · {usd(file.allows)} left
        </p>
      )}
    </div>
  );
}

function Case({ file }: { file: CaseFile }) {
  const facts = [
    ['Customer', file.customer ?? 'not on record'],
    ['Order', file.orderNo ?? '—'],
    ['RMA', file.rmaId ?? '—'],
    ['Paid with', file.paymentMethod ?? '—'],
    ['Model', file.model],
    ['Scenario', file.scenarioId],
  ];
  return (
    <>
      <h3>{file.headline}</h3>
      <p className="case-why">{file.explanation}</p>
      <Amounts file={file} />
      <dl className="case-facts">
        {facts.map(([k, v]) => (
          <div key={k}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      <Ledger file={file} />
      <div className="case-checks">
        {file.checks.map((c) => (
          <span key={c.code} className={c.severity === 'BLOCK' ? 'block' : 'hold'} title={c.code}>
            {c.check}
          </span>
        ))}
      </div>
      <div className="case-trace">
        <span>Case agent</span>
        {file.trace.map((s, i) => (
          <code key={i} className={s.ok ? '' : 'failed'}>
            {s.tool}
          </code>
        ))}
        <em>Read-only store tools · no approve tool · never reads the e-mail</em>
      </div>
    </>
  );
}

export function CaseFileWidget(params: AgWidgetParams<CaseWidget>) {
  const ids = useCallIds(params);
  const [index, setIndex] = useState(0);
  const count = ids?.length ?? 0;
  const callId = ids && count ? ids[Math.min(index, count - 1)] : null;
  const state = useSyncExternalStore(
    caseStore.subscribe,
    () => (callId ? caseStore.get(callId) : undefined),
    () => undefined,
  );

  useEffect(() => {
    if (callId) requestCase(callId);
  }, [callId]);

  const step = (d: number) => setIndex((i) => (Math.min(i, count - 1) + d + count) % count);
  const decision = state?.status === 'done' ? state.file.decision : null;

  return (
    <div className="case">
      <div className="case-bar">
        <button onClick={() => step(-1)} disabled={count < 2} aria-label="Previous case">
          ‹
        </button>
        <span>{ids === null ? 'Loading…' : count ? `Case ${Math.min(index, count - 1) + 1} of ${count}` : 'No held or blocked calls'}</span>
        <button onClick={() => step(1)} disabled={count < 2} aria-label="Next case">
          ›
        </button>
        {decision && <b className={decision === 'BLOCK' ? 'block' : 'hold'}>{decision}</b>}
      </div>
      <div className="case-body">
        {state?.status === 'working' && <p className="case-wait">The case agent is reading the store record…</p>}
        {state?.status === 'failed' && <p className="case-wait">Could not build this case: {state.error}</p>}
        {state?.status === 'done' && <Case file={state.file} />}
      </div>
      <a className="case-demo" href={DEMO} target="_blank" rel="noopener">
        Approve or reject a held call yourself in the live demo →
      </a>
    </div>
  );
}

export const CASE_WIDGET: AgWidgetDefinition<string, CaseWidget> = {
  id: 'case-file',
  label: 'Case file',
  comp: CaseFileWidget,
  dataMapping: { callKey: { type: 'fieldset', supportedRoles: ['category'], intent: 'category' } },
  form: (p) => p.createDefaults({ dataMappingItems: [{ key: 'callKey', label: 'Call' }] }),
  defaultSize: { width: 10, height: 30 },
  minSize: { width: 6, height: 20 },
};
