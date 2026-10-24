'use client';

// HOMI's returns control: one AG Studio instance over the exported evaluation data, under a header
// that states the result in one line. The page is static: it fetches public/counterfoil-data.json
// in the browser, so it can be hosted anywhere with no credentials.

import { useEffect, useMemo, useRef, useState } from 'react';
import { enableStudioDevValidations, type AgStudioApi } from 'ag-studio';
import { AgStudio, AgStudioProvider } from 'ag-studio-react';
import { counterfoilReport, PAGE_TITLES } from './report';
import { buildStudioData, type CounterfoilData } from './studio-data';
import { Store3D } from './store-3d';
import { counterfoilTheme } from './theme';

if (process.env.NODE_ENV !== 'production') {
  enableStudioDevValidations();
}

// Optional. Without a key AG Studio shows a watermark, which the AG Grid team says is fine for judging.
const LICENSE_KEY = process.env.NEXT_PUBLIC_AG_STUDIO_LICENSE || undefined;

const CONDITIONS = [
  { label: 'No gate', note: 'agent calls Braintree directly' },
  { label: '$200 cap', note: 'tool allowlist + per-transaction cap' },
  { label: 'Counterfoil', note: "checked against the store's records" },
];

// Attack runs where wrong money reached the rail, per condition.
function harmByCondition(data: CounterfoilData) {
  return CONDITIONS.map(({ label, note }) => {
    const attacks = data.runs.filter((r) => r.condition === label && r.attackRun === 1);
    const harm = attacks.filter((r) => r.harm === 1).length;
    return { label, note, harm, total: attacks.length };
  });
}

export default function Page() {
  const [data, setData] = useState<CounterfoilData | null>(null);
  const [error, setError] = useState('');
  const [pageId, setPageId] = useState(counterfoilReport.selectedPageId);
  const apiRef = useRef<AgStudioApi | null>(null);

  useEffect(() => {
    fetch('counterfoil-data.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const studioData = useMemo(() => (data ? buildStudioData(data) : null), [data]);
  const compare = useMemo(() => (data ? harmByCondition(data) : []), [data]);
  const models = useMemo(() => (data ? [...new Set(data.runs.map((r) => String(r.model)))] : []), [data]);

  // Studio leaves page navigation to the host: switching pages is a state change.
  const openPage = (id: string) => {
    const api = apiRef.current;
    if (!api) return;
    api.setState({ ...api.getState(), selectedPageId: id });
    setPageId(id);
  };

  return (
    <>
      <header className="top">
        <div className="brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="homi-logo.png" alt="HOMI" />
          <span className="divider" />
          <b>Returns control</b>
          <span className="pill">powered by Counterfoil</span>
        </div>
        <a className="live" href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">Try it live →</a>
        <nav>
          {counterfoilReport.pages.map((p) => (
            <button key={p.id} className={p.id === pageId ? 'active' : ''} onClick={() => openPage(p.id)}>
              {PAGE_TITLES[p.id] ?? p.id}
            </button>
          ))}
        </nav>
      </header>

      <Store3D />

      {data && (
        <section className="hero">
          <div>
            <span className="eyebrow">AI agents handle refunds · Braintree sandbox</span>
            <h1>Hidden instructions moved the agent. Counterfoil kept the money where the store&apos;s records say.</h1>
            <p>
              Each attack e-mail tries to make the store&apos;s AI agent refund or charge the wrong amount. These are the
              attack runs where that wrong money actually reached Braintree.
            </p>
          </div>
          <div className="compare">
            {compare.map((c) => (
              <div key={c.label} className={`cond ${c.label === 'Counterfoil' ? 'us' : ''}`}>
                <small>{c.label}</small>
                <strong className={c.harm ? 'bad' : 'good'}>
                  {c.harm}/{c.total}
                </strong>
                <em>{c.note}</em>
              </div>
            ))}
          </div>
        </section>
      )}

      <main>
        {error && <p className="message">Could not load counterfoil-data.json ({error}). Run scripts/export_dashboard.py first.</p>}
        {!error && !studioData && <p className="message">Loading…</p>}
        {studioData && (
          <AgStudioProvider licenseKey={LICENSE_KEY}>
            <AgStudio
              style={{ height: '100%', width: '100%' }}
              theme={counterfoilTheme}
              layout={{ widgetBorderEnabled: true }}
              data={studioData}
              initialState={counterfoilReport}
              mode="view"
              onApiReady={(e) => {
                apiRef.current = e.api;
              }}
            />
          </AgStudioProvider>
        )}
      </main>

      {data && (
        <footer>
          {data.runs.length} runs · models: {models.join(', ')} · exported {data.asOf.slice(0, 16).replace('T', ' ')} UTC ·
          HOMI is a fictional store built for this demo; payments run in the Braintree sandbox with mocked PayPal.
        </footer>
      )}
    </>
  );
}
