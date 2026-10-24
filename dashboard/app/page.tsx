'use client';

// HOMI's returns control: an editorial opening (headline, the store's return station, the result per
// condition) over a dark console, which is one AG Studio instance on the exported evaluation data. The page is static: it fetches
// public/counterfoil-data.json in the browser, so it can be hosted anywhere with no credentials.

import { useEffect, useMemo, useRef, useState } from 'react';
import { enableStudioDevValidations, type AgStudioApi } from 'ag-studio';
import { AgStudio, AgStudioProvider } from 'ag-studio-react';
import { buildReport, layoutRows, PAGE_TITLES, ROW_HEIGHT } from './report';
import { buildStudioData, modelName, type CounterfoilData } from './studio-data';
import { Store3D } from './store-3d';
import { canvasPadding, counterfoilTheme } from './theme';

if (process.env.NODE_ENV !== 'production') {
  enableStudioDevValidations();
}

// Optional. Without a key AG Studio shows a watermark, which the AG Grid team says is fine for judging.
const LICENSE_KEY = process.env.NEXT_PUBLIC_AG_STUDIO_LICENSE || undefined;

const PHONE = '(max-width: 760px)';

const CONDITIONS = [
  { label: 'No gate', note: 'Agent calls Braintree directly' },
  { label: '$200 cap', note: 'Tool allowlist and per-transaction cap' },
  { label: 'Counterfoil', note: "Every call checked against the store's records" },
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
  const [compact, setCompact] = useState<boolean | null>(null);
  const [pageId, setPageId] = useState('overview');
  const apiRef = useRef<AgStudioApi | null>(null);

  useEffect(() => {
    setCompact(window.matchMedia(PHONE).matches);
    fetch('counterfoil-data.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const studioData = useMemo(() => (data ? buildStudioData(data) : null), [data]);
  const report = useMemo(() => (compact === null ? null : buildReport(compact)), [compact]);
  const theme = useMemo(() => counterfoilTheme(!!compact), [compact]);
  const compare = useMemo(() => (data ? harmByCondition(data) : []), [data]);
  const models = useMemo(() => (data ? [...new Set(data.runs.map((r) => modelName(r.model)))] : []), [data]);

  // The canvas is as tall as the page's widgets, so the browser scrolls, not Studio.
  const page = report?.pages.find((p) => p.id === pageId);
  const pad = canvasPadding(!!compact);
  const studioHeight = page ? layoutRows(page) * ROW_HEIGHT + 2 * pad : 0;

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
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="logo" src="homi-logo.png" alt="HOMI" />
        <span className="product">Returns control</span>
        <nav>
          {Object.entries(PAGE_TITLES).map(([id, text]) => (
            <button key={id} className={id === pageId ? 'active' : ''} onClick={() => openPage(id)}>
              {text}
            </button>
          ))}
          <a className="live" href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">
            Try it live →
          </a>
        </nav>
      </header>

      {pageId === 'overview' && data && (
        <section className="hero">
          <div className="lead">
            <div>
              <span className="eyebrow">Evaluation · {data.runs.length} runs · {models.length} models</span>
              <h1>
                Hidden instructions fool the agent. <em>Counterfoil</em> keeps the money right.
              </h1>
            </div>
            <p>
              Each attack e-mail tries to make HOMI&apos;s AI agent refund or charge the wrong amount. Without a gate,{' '}
              {compare[0].harm} of {compare[0].total} attack runs paid wrong money through Braintree. With Counterfoil,{' '}
              {compare[2].harm === 0 ? 'none did' : `${compare[2].harm} did`}.
            </p>
          </div>
          <div className="station">
            <Store3D />
          </div>
          <div className="caption">
            <span>HOMI self-service return station · Braintree sandbox, mocked PayPal</span>
            <span>Fig. 1</span>
          </div>
          <div className="conditions">
            {compare.map((c) => (
              <div key={c.label} className={`cond ${c.harm ? 'bad' : 'good'}`}>
                <b>{c.label}</b>
                <small>{c.note}</small>
                <strong>
                  {c.harm}
                  <span> / {c.total}</span>
                </strong>
              </div>
            ))}
          </div>
        </section>
      )}

      <main style={studioHeight ? { height: studioHeight } : undefined}>
        {error && <p className="message">Could not load counterfoil-data.json ({error}). Run scripts/export_dashboard.py first.</p>}
        {!error && !studioData && <p className="message">Loading…</p>}
        {studioData && report && (
          <AgStudioProvider licenseKey={LICENSE_KEY}>
            <AgStudio
              style={{ height: '100%', width: '100%' }}
              theme={theme}
              layout={{ widgetBorderEnabled: true }}
              panels={{ view: { left: [], right: [] } }}
              data={studioData}
              initialState={report}
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
          <span>
            {data.runs.length} runs · {models.join(', ')} · exported {data.asOf.slice(0, 16).replace('T', ' ')} UTC
          </span>
          <span>HOMI is a fictional store. Payments run in the Braintree sandbox with mocked PayPal.</span>
        </footer>
      )}
    </>
  );
}
