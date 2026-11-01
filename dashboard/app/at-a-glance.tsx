// The results at a glance (1 Nov): a band of headline numbers under the hero, and a comparison table after the simple story,
// so a reader sees the measured difference without opening "Technical details". Measured cells are computed from
// counterfoil-data.json (simulation runs only, as in the results band); the buyer-side column describes what those guards check.

import { modelName, type CounterfoilData } from './studio-data';
import styles from './at-a-glance.module.css';

type Run = CounterfoilData['runs'][number];
type Mark = 'strong' | 'tradeoff' | 'short' | 'none';

const simulated = (data: CounterfoilData) => data.runs.filter((r) => !String(r.source).includes('braintree'));

function tally(runs: Run[], condition: string) {
  const mine = runs.filter((r) => r.condition === condition);
  const attacks = mine.filter((r) => r.attackRun === 1);
  const clean = mine.filter((r) => r.cleanRun === 1);
  return {
    harm: attacks.filter((r) => r.harm === 1).length,
    attacks: attacks.length,
    cleanDone: clean.filter((r) => r.cleanDone === 1).length,
    clean: clean.length,
  };
}

const pct = (n: number, d: number) => (d ? `${Math.round((100 * n) / d)}%` : '–');

function openResults() {
  const results = document.getElementById('crew-results') as HTMLDetailsElement | null;
  if (results) results.open = true;
}

export function StatBand({ data }: { data: CounterfoilData }) {
  const runs = simulated(data);
  const gate = tally(runs, 'Counterfoil');
  const none = tally(runs, 'No gate');
  const models = new Set(runs.map((r) => modelName(r.model))).size;
  return (
    <section className={styles.band} aria-label="Results at a glance">
      <div className={styles.plum}>
        <strong>{gate.harm}<small>/{gate.attacks}</small></strong>
        <span>attack runs where wrong money moved, with Counterfoil</span>
      </div>
      <div className={styles.salmon}>
        <strong>{none.harm}<small>/{none.attacks}</small></strong>
        <span>the same attacks with no gate</span>
      </div>
      <div className={styles.pink}>
        <strong>{pct(gate.cleanDone, gate.clean)}</strong>
        <span>genuine requests still handled right</span>
      </div>
      <div className={styles.sky}>
        <strong>{models}</strong>
        <span>AI models tested, local and cloud</span>
      </div>
      <p className={styles.bandNote}>
        Simulation · {runs.length} completed runs · exported {data.asOf.slice(0, 10)}.{' '}
        <a href="#crew-results" onClick={openResults}>How we measured ↓</a>
      </p>
    </section>
  );
}

type Cell = [Mark, string];
const COLUMNS = ['No gate', '$200 cap', 'Buyer-side guards', 'Counterfoil'];

export function CompareTable({ data }: { data: CounterfoilData }) {
  const runs = simulated(data);
  const [none, cap, gate] = ['No gate', '$200 cap', 'Counterfoil'].map((c) => tally(runs, c));
  const rows: { label: string; cells: Cell[] }[] = [
    {
      label: 'Wrong money in our attack runs',
      cells: [
        ['short', `${none.harm} of ${none.attacks}`],
        ['short', `${cap.harm} of ${cap.attacks}`],
        ['none', 'Not tested by us'],
        ['strong', `${gate.harm} of ${gate.attacks}`],
      ],
    },
    {
      label: 'Genuine requests handled right',
      cells: [
        ['tradeoff', pct(none.cleanDone, none.clean)],
        ['tradeoff', pct(cap.cleanDone, cap.clean)],
        ['none', 'Not tested by us'],
        ['strong', pct(gate.cleanDone, gate.clean)],
      ],
    },
    {
      label: 'Checks this order’s record',
      cells: [
        ['short', 'No'],
        ['short', 'No'],
        ['short', 'No'],
        ['strong', 'Owner, return, earlier refunds'],
      ],
    },
    {
      label: 'Tells an owed $60 from one that isn’t',
      cells: [
        ['short', 'No'],
        ['short', 'No, only the amount'],
        ['tradeoff', 'Only what the user signed'],
        ['strong', 'Yes, against the return record'],
      ],
    },
    {
      label: 'When a person looks',
      cells: [
        ['short', 'Never'],
        ['tradeoff', 'Above the cap'],
        ['tradeoff', 'Above a threshold'],
        ['strong', 'When a check or store rule flags it'],
      ],
    },
    {
      label: 'Built for',
      cells: [
        ['none', '–'],
        ['none', 'Either side'],
        ['none', 'An agent spending for a buyer'],
        ['none', 'A store giving money back'],
      ],
    },
  ];
  return (
    <section className={styles.compare} aria-labelledby="compare-title">
      <span className="review-eyebrow">WHY NOT JUST A CAP?</span>
      <h2 id="compare-title">The cost of the alternatives.</h2>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <td />
              {COLUMNS.map((c) => <th key={c} scope="col" className={c === 'Counterfoil' ? styles.ours : undefined}>{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {row.cells.map(([mark, text], i) => (
                  <td key={COLUMNS[i]} data-col={COLUMNS[i]} className={COLUMNS[i] === 'Counterfoil' ? styles.ours : undefined}>
                    <span className={styles.cell}>
                      {mark !== 'none' && <i className={styles[mark]} aria-hidden="true" />}
                      {text}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={styles.legend}>
        <span><i className={styles.strong} aria-hidden="true" />Strong</span>
        <span><i className={styles.tradeoff} aria-hidden="true" />Trade-off</span>
        <span><i className={styles.short} aria-hidden="true" />Falls short</span>
      </p>
      <p className={styles.compareNote}>
        No gate, the $200 cap and Counterfoil were run on the same attacks and genuine requests (simulation, {runs.length} runs).
        Buyer-side guards are spend caps, allowlists, signed intent and human approval over a cap; we did not run them, so that
        column says what they check, from our October 2026 scan.
      </p>
    </section>
  );
}
