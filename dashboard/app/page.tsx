'use client';

// HOMI's returns control in felt (Codex's design, 25 Oct): the hero with Counterfoil, the result per condition, the return
// crew, the 3D story, then the evidence: one AG Studio instance on the exported evaluation data, and the 3D model chart.
// The page is static: it fetches public/counterfoil-data.json in the browser, so it can be hosted anywhere with no credentials.

import { useEffect, useMemo, useRef, useState } from 'react';
import { enableStudioDevValidations, type AgStudioApi } from 'ag-studio';
import { AgStudio, AgStudioProvider, createWidgets } from 'ag-studio-react';
import { buildReport, layoutRows, PAGE_TITLES, ROW_HEIGHT } from './report';
import { buildStudioData, modelName, type CounterfoilData } from './studio-data';
import { SOFT_WIDGETS } from './soft-charts';
import { CASE_WIDGET } from './case-file';
import { buildCaseHarness } from './case-agent';
import { Story3D, StoryStrip } from './story-3d';
import { ClosingBand, Crew, FollowingFoil, Hero, ResultBand, StoryAside } from './felt';
import { ModelBars3D } from './model-bars-3d';
import { canvasPadding, counterfoilTheme } from './theme';

if (process.env.NODE_ENV !== 'production') {
  enableStudioDevValidations();
}

// Optional. Without a key AG Studio shows a watermark, which the AG Grid team says is fine for judging.
const LICENSE_KEY = process.env.NEXT_PUBLIC_AG_STUDIO_LICENSE || undefined;

const PHONE = '(max-width: 760px)';

// Studio's widgets plus our own: the soft charts (./soft-charts.tsx) and the case file (./case-file.tsx).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const WIDGETS = createWidgets<any>({ additionalTypes: [...SOFT_WIDGETS, CASE_WIDGET] } as never);

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
        <span className="wordmark">HOMI</span>
        <nav>
          {Object.entries(PAGE_TITLES).map(([id, text]) => (
            <button key={id} className={id === pageId ? 'active' : ''} onClick={() => openPage(id)}>
              {text}
            </button>
          ))}
        </nav>
        <span className="sandbox">Sandbox</span>
        <a className="live f-patch" href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="buttons/try-it-live-plum.webp" alt="Try it live" />
        </a>
      </header>

      {pageId === 'overview' && data && (
        <>
          <Hero onStory={() => document.getElementById('story')?.scrollIntoView({ behavior: 'smooth', block: 'start' })} />
          <ResultBand compare={compare} runs={data.runs.length} models={models.length} />
          <Crew />
          <section className="f-story felt" id="story">
            <h2>One receipt. Seven moments.</h2>
            <p className="f-sub">Follow attack P6-01 from checkout to resolution, one button at a time.</p>
            <div className="f-story-grid">
              <div className="station">
                <Story3D />
              </div>
              <StoryAside />
            </div>
            <StoryStrip />
            <p className="f-note">The blocked $60 and the new, valid $40 are separate requests · Braintree sandbox, mocked PayPal</p>
          </section>
          <section className="f-evidence-head">
            <h2>The evidence, without the guesswork.</h2>
            <p className="f-sub">Every run of the evaluation: filter by model, scenario or outcome and see what each agent tried and what reached Braintree.</p>
          </section>
        </>
      )}

      {pageId === 'review' && (
        <section className="intro felt">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="intro-foil" src="crew/counterfoil-block.webp" alt="" />
          <p>
            Every refund or charge Counterfoil did not let straight through. <b>APPROVAL</b> waits for the merchant; <b>BLOCK</b> never
            reaches Braintree. Step through the cases on the right, or narrow them with the buttons: the case agent reads the store
            record and lays each call out next to what the record allows. It cannot approve anything.
          </p>
          <a href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">
            Approve a held call in the live demo →
          </a>
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
              layout={{ widgetBorderEnabled: false }}
              panels={{ view: { left: [], right: [] } }}
              widgets={WIDGETS}
              data={studioData}
              initialState={report}
              mode="view"
              onApiReady={(e) => {
                apiRef.current = e.api;
                // The case agent runs in view mode, where Studio has no assistant panel, so it is built here, not via `ai`.
                buildCaseHarness(e.api);
              }}
            />
          </AgStudioProvider>
        )}
      </main>

      {/* The console's model table, again in 3D, under it. Desktop only: phones keep just the table. */}
      {pageId === 'overview' && data && compact === false && (
        <section className="bars3d-section">
          <div className="bars3d-head">
            <div>
              <h2>Wrong money paid, by model.</h2>
              <p className="f-sub">Every run, attack and clean, counted like the table above · drag to turn, hover a bar</p>
            </div>
            <FollowingFoil src="crew/counterfoil-complete.webp" alt="" />
          </div>
          <ModelBars3D data={data} />
        </section>
      )}

      {pageId === 'overview' && data && <ClosingBand />}

      {data && (
        <footer>
          <span className="wordmark small">HOMI</span>
          <span>Fictional store · Braintree sandbox · No real funds</span>
          <span>
            {data.runs.length} runs · {models.join(', ')} · exported {data.asOf.slice(0, 16).replace('T', ' ')} UTC
          </span>
        </footer>
      )}
    </>
  );
}
