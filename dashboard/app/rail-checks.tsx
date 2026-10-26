'use client';

// The Overview's rail-side checks: what Braintree itself was asked, recorded on the sandbox by
// scripts/record_rail_checks.py and exported as `railChecks`. The refund sweep (counterfoil/reconcile.py) looks for
// money that left through Braintree without the store's ledger knowing; the three columns are what Braintree refuses
// on its own (the live demo's section 4). Shown exactly as recorded, with the sandbox ids.

import type { CounterfoilData } from './studio-data';

type Step = {
  label: string;
  ok: boolean;
  id?: string;
  status?: string;
  error?: string;
  gate?: string;
  disputes?: { id: string; status: string; kind: string; amount: string }[];
  findings?: { code: string; severity: string; detail: string }[];
};
type Unknown = { order_no: string; rail_total: string; store_total: string; difference: string; refunds_the_store_does_not_list: string[] };
export type RailChecks = {
  recordedAt: string;
  sweep: {
    since: string;
    seen: number;
    throughGate: { orderNo: string; amount: string; decision: string; railId: string | null };
    behindTheGate: { orderNo: string; amount: string; ok: boolean; railId: string | null };
    unknown: Unknown[];
    foreign: { id: string }[];
    credits: { id: string }[];
  };
  railRules: { card: Step[]; paypal: Step[]; dispute: Step[] };
};

const COLUMNS: { key: keyof RailChecks['railRules']; title: string; sub: string }[] = [
  { key: 'card', title: 'Test card', sub: 'settled with testing.settle_transaction' },
  { key: 'paypal', title: 'Mocked PayPal', sub: 'the sandbox enforces no refund limit' },
  { key: 'dispute', title: 'Dispute test card', sub: '4023 8984 9398 8028' },
];

function tag(s: Step): [string, string] {
  if (s.gate) return [s.gate, s.gate === 'BLOCK' ? 'no' : 'hold'];
  return s.ok ? ['OK', 'ok'] : ['REFUSED', 'no'];
}

function RuleStep({ s }: { s: Step }) {
  const [text, cls] = tag(s);
  const why = s.error ?? s.findings?.filter((f) => f.severity !== 'PASS').map((f) => f.code).join(', ');
  return (
    <li>
      <span className={`rc-tag ${cls}`}>{text}</span>
      <span className="rc-label">{s.label}</span>
      {why && <small>{why}</small>}
      {s.disputes?.map((d) => (
        <small key={d.id}>
          {d.kind} · {d.status} · {d.amount}
        </small>
      ))}
    </li>
  );
}

export function RailChecksBoard({ data }: { data: CounterfoilData }) {
  const rc = data.railChecks;
  if (!rc) return null;
  const { sweep } = rc;
  const day = new Date(rc.recordedAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  return (
    <section className="rc">
      <p className="ev-meta">Braintree sandbox · recorded {day}</p>
      <div className="rc-sweep felt">
        <h3>Refund sweep</h3>
        <p className="rc-lead">
          One <code>transaction.search</code> for every refund Braintree sent out, matched against the store&apos;s ledger. A refund made
          in the Braintree Control Panel or by another tool shows up here, even if nobody asks to refund that order again.
        </p>
        <ol className="rc-flow">
          <li>
            <b>Through Counterfoil</b>
            <span>
              {sweep.throughGate.amount} on {sweep.throughGate.orderNo} · {sweep.throughGate.decision.split('/')[0]}
            </span>
            <code>{sweep.throughGate.railId}</code>
          </li>
          <li>
            <b>Straight on Braintree</b>
            <span>
              {sweep.behindTheGate.amount} on {sweep.behindTheGate.orderNo} · the store is not told
            </span>
            <code>{sweep.behindTheGate.railId}</code>
          </li>
          <li className={sweep.unknown.length ? 'found' : ''}>
            <b>Sweep</b>
            {sweep.unknown.length === 0 && <span>{sweep.seen} refunds on Braintree, all in the ledger</span>}
            {sweep.unknown.map((u) => (
              <span key={u.order_no}>
                {u.order_no}: Braintree {u.rail_total}, ledger {u.store_total} → <strong>{u.difference} unknown</strong>
              </span>
            ))}
            {sweep.unknown.flatMap((u) => u.refunds_the_store_does_not_list).map((id) => (
              <code key={id}>{id}</code>
            ))}
          </li>
        </ol>
        <p className="rc-foot">
          The gate&apos;s own refund passed and is in the ledger, so it is not reported. Refunds on other stores&apos; sales and standalone
          credits are listed too: {sweep.foreign.length + sweep.credits.length} this time.
        </p>
      </div>

      <div className="rc-rules">
        <h3>What Braintree refuses on its own</h3>
        <p className="rc-lead">Counterfoil leaves these to Braintree and checks what Braintree lets through.</p>
        <div className="rc-cols">
          {COLUMNS.map((c) => (
            <div className="rc-col felt" key={c.key}>
              <h4>{c.title}</h4>
              <p className="rc-sub">{c.sub}</p>
              <ul>
                {rc.railRules[c.key].map((s, i) => (
                  <RuleStep s={s} key={i} />
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
