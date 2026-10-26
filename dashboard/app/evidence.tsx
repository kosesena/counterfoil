'use client';

// The Overview's evidence board (Codex's felt palette v3, docs/gorseller/site-tasarim/evidence-palette-v3/): a gate and
// a model filter, three tiles for the chosen gate, and the wrong-money count of every model on the dev and holdout sets,
// one felt bar per gate (Codex's strips, docs/gorseller/site-tasarim/bar-strips-v1, as border-images in globals.css). Everything is counted from counterfoil-data.json, which holds the latest-gate runs only; the
// Braintree sandbox run is shown on its own line, not mixed into the dev bars.

import { useMemo, useState } from 'react';
import { modelName, type CounterfoilData } from './studio-data';

type Run = Record<string, unknown>;
const GATES = ['Counterfoil', '$200 cap', 'No gate'] as const;
type Gate = (typeof GATES)[number];
const BAR_ORDER: Gate[] = ['No gate', '$200 cap', 'Counterfoil'];
const GATE_CLASS: Record<Gate, string> = { 'No gate': 'none', '$200 cap': 'cap', Counterfoil: 'cf' };

// every model the evaluation has used, in the order Codex's design lists them
const MODELS = ['Claude Haiku 4.5', 'Claude Opus 5.5', 'Claude Sonnet 5', 'GPT-5.6 Sol', 'GPT-5.6 Terra', 'Hermes 3', 'Llama 3.1', 'Qwen 2.5', 'Qwen 3'];

const sandbox = (r: Run) => String(r.source).includes('braintree');
const split = (r: Run) => (String(r.source).includes('holdout') ? 'holdout' : 'dev');
const count = (runs: Run[], field: string) => runs.reduce((n, r) => n + (r[field] === 1 ? 1 : 0), 0);
const pct = (n: number, d: number) => (d ? `${Math.round((100 * n) / d)}%` : '—');

function Tile({ title, value, note }: { title: string; value: string; note: string }) {
  return (
    <div className="ev-tile felt">
      <h3>{title}</h3>
      <strong className={value === 'Pending' ? 'pending' : ''}>{value}</strong>
      <span>{note}</span>
    </div>
  );
}

function Panel({ title, runs, models }: { title: string; runs: Run[]; models: string[] }) {
  const rows = models.filter((m) => runs.some((r) => modelName(r.model) === m));
  return (
    <section className="ev-panel felt">
      <header>
        <h3>{title}</h3>
        <ul className="ev-legend" aria-label="Legend">
          {BAR_ORDER.map((g) => (
            <li key={g}>
              <i className={GATE_CLASS[g]} />
              {g}
            </li>
          ))}
        </ul>
      </header>
      {rows.length === 0 && <p className="ev-empty">No latest-gate runs for this model on this set yet.</p>}
      {rows.map((m) => (
        <div className="ev-row" key={m}>
          <b>{m}</b>
          <div className="ev-bars">
            {BAR_ORDER.map((g) => {
              const attacks = runs.filter((r) => modelName(r.model) === m && r.condition === g && r.attackRun === 1);
              const harm = count(attacks, 'harm');
              return (
                <div className="ev-bar" key={g} role="img" aria-label={`${m}, ${g}: ${harm} of ${attacks.length}`}>
                  <span className="ev-lane">
                    <span className="ev-track" />
                    {harm > 0 && <span className={`ev-fill ${GATE_CLASS[g]}`} style={{ width: `${(100 * harm) / (attacks.length || 1)}%` }} />}
                  </span>
                  <em>
                    {harm} / {attacks.length}
                    <small>{pct(harm, attacks.length)}</small>
                  </em>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </section>
  );
}

export function EvidenceBoard({ data }: { data: CounterfoilData }) {
  const [gate, setGate] = useState<Gate>('Counterfoil');
  const [model, setModel] = useState('All');

  const runs = useMemo(() => data.runs.filter((r) => !sandbox(r)), [data]);
  const ran = useMemo(() => new Set(runs.map((r) => modelName(r.model))), [runs]);
  const pending = MODELS.filter((m) => !ran.has(m));
  const picked = model === 'All' ? runs : runs.filter((r) => modelName(r.model) === model);
  const shown = model === 'All' ? MODELS : [model];

  const atGate = picked.filter((r) => r.condition === gate);
  const attacks = atGate.filter((r) => r.attackRun === 1);
  const clean = atGate.filter((r) => r.cleanRun === 1);
  const none = attacks.length === 0;
  const sets = [...new Set(picked.map(split))].sort().join(' + ') || 'no runs yet';

  const box = data.runs.filter(sandbox);
  const boxModel = box.length ? modelName(box[0].model) : '';
  const day = new Date(data.asOf).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <section className="ev">
      <p className="ev-meta">
        Latest gate · {runs.length} runs · exported {day}
      </p>
      <div className="ev-filters">
        <div className="ev-filter felt" role="group" aria-label="Gate condition">
          <h3>Gate condition</h3>
          <div className="ev-pills">
            {GATES.map((g) => (
              <button key={g} className={g === gate ? 'on' : ''} aria-pressed={g === gate} onClick={() => setGate(g)}>
                {g}
              </button>
            ))}
          </div>
        </div>
        <div className="ev-filter felt" role="group" aria-label="Model">
          <h3>Model</h3>
          <div className="ev-pills">
            {['All', ...MODELS].map((m) => (
              <button
                key={m}
                className={`${m === model ? 'on' : ''} ${pending.includes(m) ? 'later' : ''}`}
                aria-pressed={m === model}
                onClick={() => setModel(m)}
              >
                {m}
              </button>
            ))}
          </div>
          {pending.length > 0 && <p className="ev-foot">{pending.join(', ')}: latest-gate runs pending</p>}
        </div>
      </div>

      <div className="ev-tiles">
        <Tile title="Agent misled" value={none ? 'Pending' : pct(count(attacks, 'agentMisled'), attacks.length)} note={`followed the attacker · ${gate}`} />
        <Tile
          title="Wrong money paid"
          value={none ? 'Pending' : `${count(attacks, 'harm')} / ${attacks.length}`}
          note={`reached Braintree · ${gate} · ${sets}`}
        />
        <Tile title="Genuine requests" value={clean.length ? pct(count(clean, 'cleanDone'), clean.length) : 'Pending'} note={`handled right · ${gate}`} />
      </div>

      <div className="ev-panels">
        <Panel title="Dev · wrong-money cases" runs={runs.filter((r) => split(r) === 'dev')} models={shown} />
        <Panel title="Holdout · wrong-money cases" runs={runs.filter((r) => split(r) === 'holdout')} models={shown} />
      </div>

      {box.length > 0 && (
        <p className="ev-sandbox felt">
          <b>Braintree sandbox · {boxModel}</b>
          {BAR_ORDER.map((g) => {
            const a = box.filter((r) => r.condition === g && r.attackRun === 1);
            return (
              <span key={g}>
                {g} {count(a, 'harm')} / {a.length}
              </span>
            );
          })}
          <small>Real sandbox sales and refunds, mocked PayPal</small>
        </p>
      )}
    </section>
  );
}
