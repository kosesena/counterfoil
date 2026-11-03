'use client';
import { useEffect, useState } from 'react';
import styles from './recent-evidence.module.css';

type Condition = {
  condition: string; label: string; runs: number; moneyHarm: number; recordHarm: number;
  error: number; unknown: number; autoEligible: number; reviewEligible: number; completed: number;
  validHeld: number; reviewUnpaid: number; explicitReview: number; policyBypass: number;
};
type Cohort = {
  id: string; title: string; description: string; limits: string; kind: 'attack' | 'clean';
  status: string; cases: number; runs: number; models: string[]; rail: string; date: string;
  commit: string | null; conditions: Condition[]; download: string;
};
type Evidence = { measuredThrough: string; cohorts: Cohort[] };
type Metric = { label: string; note: string; value: (c: Condition) => string };
const fraction = (n: number, d: number) => d ? `${n} / ${d}` : '—';
const shared: Metric[] = [
  { label: 'Confirmed record violations', note: 'Payments or reads that violate trusted store records or policy.', value: c => fraction(c.recordHarm, c.runs) },
  { label: 'Errors', note: 'Run or agent errors, separate from outcomes.', value: c => String(c.error) },
  { label: 'Unknown payment outcomes', note: 'Unresolved outcomes never count as successful defenses.', value: c => String(c.unknown) },
];
const clean: Metric[] = [
  { label: 'Requested refunds completed', note: 'Exact requested amount, for requests eligible for automatic payment.', value: c => fraction(c.completed, c.autoEligible) },
  { label: 'Valid refund calls held', note: 'A matching automatic refund was held before payment; abstention is separate.', value: c => fraction(c.validHeld, c.autoEligible) },
  { label: 'Review-required requests: no payment', note: 'Includes model abstention, not necessarily a gate intervention.', value: c => fraction(c.reviewUnpaid, c.reviewEligible) },
  { label: 'Explicit human-review hand-offs', note: 'A matching call received APPROVAL without payment.', value: c => fraction(c.explicitReview, c.reviewEligible) },
  { label: 'Payments without required confirmation', note: 'A policy bypass even when the requested amount matches.', value: c => fraction(c.policyBypass, c.reviewEligible) },
];

export function RecentEvidence() {
  const [data, setData] = useState<Evidence | null>(null);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState('hosted-attacks');
  useEffect(() => {
    const controller = new AbortController();
    fetch('recent-evidence.json', { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then(setData).catch(e => { if (e.name !== 'AbortError') setError(true); });
    return () => controller.abort();
  }, []);
  const cohort = data?.cohorts.find(c => c.id === selected);
  const metrics: Metric[] = cohort?.kind === 'clean' ? [...clean, ...shared] : [
    { label: 'Money or data harm', note: 'Original outcome metric; narrower than the record-policy check.', value: c => fraction(c.moneyHarm, c.runs) },
    ...shared,
    ...(cohort?.id === 'hosted-attacks' ? [{ label: 'Full USD 100 refund completed', note: 'Partial refunds are not automatically harmful, but are not full-entitlement completion.', value: (c: Condition) => fraction(c.completed, c.runs) }] : []),
  ];
  return <section id="recent-evidence" className={styles.section} aria-labelledby="recent-title">
    <p className={styles.eyebrow}>NOVEMBER FOLLOW-UP · RECORDED EXPERIMENTS</p>
    <h2 id="recent-title">What happened in the newer tests?</h2>
    <p className={styles.intro}>Blind attacks, ordinary requests and repeated decisions, each with its own denominator.
      These results are separate from the October multi-model comparison above.</p>
    {error ? <p role="alert">The newer results could not be loaded. Reload the page to try again.</p>
      : !cohort || !data ? <p role="status">Loading recorded experiments…</p> : <>
      <div className={styles.selector}>
        <label htmlFor="evidence-cohort">Choose an experiment</label>
        <select id="evidence-cohort" value={selected} onChange={e => setSelected(e.target.value)}>
          {data.cohorts.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
        </select>
      </div>
      <article key={cohort.id} className={styles.card}>
        <div className={styles.heading}>
          <div><p className={styles.meta}>{cohort.date} · {cohort.rail}</p><h3>{cohort.title}</h3></div>
          <span className={cohort.status === 'complete' ? styles.complete : styles.incomplete}>
            {cohort.status === 'complete' ? 'Completed cohort' : 'Stopped · incomplete'}
          </span>
        </div>
        <p className={styles.description}>{cohort.description}</p>
        <div className={styles.facts}><span><strong>{cohort.cases}</strong> distinct cases</span>
          <span><strong>{cohort.runs}</strong> recorded runs</span><span>{cohort.models.join(', ')}</span></div>
        <div className={styles.scroll} role="region" aria-label={`${cohort.title} results`} tabIndex={0}>
          <table><caption>Counts within this experiment only. “—” means the category does not apply.</caption>
            <thead><tr><th scope="col">Measured outcome</th>{cohort.conditions.map(c => <th key={c.condition} scope="col">{c.label}</th>)}</tr></thead>
            <tbody>{metrics.map(m => <tr key={m.label}><th scope="row">{m.label}<small>{m.note}</small></th>
              {cohort.conditions.map(c => <td key={c.condition} data-condition={c.label} className={c.condition === 'counterfoil' ? styles.ours : undefined}>{m.value(c)}</td>)}
            </tr>)}</tbody>
          </table>
        </div>
        <details className={styles.notes} open={cohort.status !== 'complete'}>
          <summary>How to read this result</summary><p>{cohort.limits}</p>
          <p>Zero observed violations is not a guarantee for future requests. Simulation and sandbox fixtures have different entitlements and are not pooled.</p>
          {cohort.commit && <p>Tested deployment: <code>{cohort.commit.slice(0, 12)}</code></p>}
        </details>
        <a className={styles.download} href={cohort.download} download>Download scored runs (JSON) <span aria-hidden="true">↓</span></a>
      </article>
    </>}
  </section>;
}
