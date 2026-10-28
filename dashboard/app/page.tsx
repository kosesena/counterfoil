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
import { ClosingBand, Crew, Hero, ResultBand, StoryAside, useFeltConditions } from './felt';
import { CrewJourney, ProductIntro } from './crew-journey';
import { EvidenceBoard } from './evidence';
import { RailChecksBoard } from './rail-checks';
import { ReviewIntro } from './review-intro';
import { SimpleStory } from './simple-story';
import { CallsWorkspace } from './calls-workspace';
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
// The Braintree sandbox run repeats dev scenarios on the real sandbox; it has its own line on the board, not a share of the totals.
const offSandbox = (data: CounterfoilData): CounterfoilData => ({ ...data, runs: data.runs.filter((r) => !String(r.source).includes('braintree')) });

function harmByCondition(data: CounterfoilData) {
  return CONDITIONS.map(({ label, note }) => {
    const attacks = offSandbox(data).runs.filter((r) => r.condition === label && r.attackRun === 1);
    const harm = attacks.filter((r) => r.harm === 1).length;
    return { label, note, harm, total: attacks.length };
  });
}

export default function Page() {
  const [data, setData] = useState<CounterfoilData | null>(null);
  const [error, setError] = useState('');
  const [storyOpen, setStoryOpen] = useState(false);
  const [compact, setCompact] = useState<boolean | null>(null);
  const [pageId, setPageId] = useState('overview');
  useFeltConditions();
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
      <header className="top crew-header">
        <button className="crew-wordmark" onClick={() => openPage('overview')} aria-label="HOMI home"><img className="wordmark-felt" src="buttons/homi-wordmark.webp" alt="HOMI" /></button>
        <nav aria-label="Main navigation">
          {Object.entries(PAGE_TITLES).map(([id, text]) => (
            <button key={id} className={id === pageId ? 'active' : ''} aria-current={id === pageId ? 'page' : undefined} onClick={() => openPage(id)}>{text}</button>
          ))}
        </nav>
        <span className="crew-sandbox">Sandbox</span>
      </header>

      {pageId === 'overview' && data && (
        <>
          <ProductIntro />
          <SimpleStory />
          <div className="story-next-wrap"><button className="continuation-next" onClick={() => { openPage('review'); window.scrollTo({ top: 0 }); }}>Next: see how the manager reviews $80 →</button></div>
          <details className="simple-disclosure"><summary>Meet the crew and explore Nella’s other tricks</summary><CrewJourney /></details>
          <details id="crew-results" className="simple-disclosure"><summary>Technical details · test results and evidence</summary>
          <div className="crew-results">
            <span className="crew-results-kicker">THE RESULTS</span>
            <h2>The boundary, measured.</h2>
            <ResultBand compare={compare} runs={offSandbox(data).runs.length} models={models.length} />
            <p className="result-scope">{data.runs.length} completed runs in total: {offSandbox(data).runs.length} simulations and {data.runs.length-offSandbox(data).runs.length} Braintree sandbox runs. Each fraction above counts attack runs within one condition, not distinct attacks. The suite contains 14 attack scenarios across 7 families.</p>
          </div>
          <details className="story-disclosure" onToggle={e=>setStoryOpen(e.currentTarget.open)}>
            <summary>See a return in the store <span>Optional · seven-step walkthrough</span></summary>
          {storyOpen && <section className="f-story felt" id="story">
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
          </section>}
          </details>
          <section className="f-evidence-head">
            <h2>The evidence, without the guesswork.</h2>
          </section>
          <EvidenceBoard data={data} />
          {data.railChecks && (
            <>
              <section className="f-evidence-head">
                <h2>Braintree, checked from both sides.</h2>
                <p className="f-sub">The money that left without the store knowing, and the refunds Braintree refuses by itself.</p>
              </section>
              <RailChecksBoard data={data} />
            </>
          )}
          </details>
          <section className="f-evidence-head f-studio-head">
            <h2>Every held call, one by one.</h2>
            <p className="f-sub">
              <b>Held for review:</b> understand why a request needs attention. <b>Agent calls:</b> see what was requested and whether a payment happened.
            </p>
            <p className="f-studio-links">
              <button onClick={() => { openPage('review'); window.scrollTo({ top: 0 }); }}>Open Held for review →</button>
              <button onClick={() => { openPage('calls'); window.scrollTo({ top: 0 }); }}>Open Agent calls →</button>
            </p>
          </section>
        </>
      )}

      {pageId === 'review' && data && <ReviewIntro data={data} onContinue={() => { openPage('calls'); window.scrollTo({ top: 0 }); }} />}
      {pageId === 'calls' && data && <CallsWorkspace data={data} onContinue={() => { openPage('overview'); window.scrollTo({ top: 0 }); }} />}

      {/* Keep Studio mounted to preserve review state inside the optional records view. */}
      <details hidden={pageId !== 'review'} className="simple-disclosure"><summary>Technical details · inspect recorded review cases</summary>
      <main id="review-workspace" aria-hidden={pageId !== 'review'} inert={pageId !== 'review'} className={pageId !== 'review' ? 'studio-off' : ''} style={studioHeight ? { height: studioHeight } : undefined}>
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
      </details>

      {pageId === 'overview' && data && <ClosingBand />}

      {data && (
        <footer>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="wordmark-felt small" src="buttons/homi-wordmark.webp" alt="HOMI" />
          <span>Fictional store · Braintree sandbox · No real funds</span>

        </footer>
      )}
    </>
  );
}
