'use client';

// One AG Studio instance over the exported evaluation data. The page is static: it fetches
// public/counterfoil-data.json in the browser, so it can be hosted anywhere with no credentials.

import { useEffect, useMemo, useRef, useState } from 'react';
import { enableStudioDevValidations, type AgStudioApi } from 'ag-studio';
import { AgStudio, AgStudioProvider } from 'ag-studio-react';
import { counterfoilReport, PAGE_TITLES } from './report';
import { buildStudioData, type CounterfoilData } from './studio-data';

if (process.env.NODE_ENV !== 'production') {
  enableStudioDevValidations();
}

// Optional. Without a key AG Studio shows a watermark, which the AG Grid team says is fine for judging.
const LICENSE_KEY = process.env.NEXT_PUBLIC_AG_STUDIO_LICENSE || undefined;

export default function Page() {
  const [data, setData] = useState<CounterfoilData | null>(null);
  const [error, setError] = useState('');
  const [pageId, setPageId] = useState(counterfoilReport.selectedPageId);
  const apiRef = useRef<AgStudioApi | null>(null);

  // Studio leaves page navigation to the host: switching pages is a state change.
  const openPage = (id: string) => {
    const api = apiRef.current;
    if (!api) return;
    api.setState({ ...api.getState(), selectedPageId: id });
    setPageId(id);
  };

  useEffect(() => {
    fetch('counterfoil-data.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const studioData = useMemo(() => (data ? buildStudioData(data) : null), [data]);

  return (
    <>
      <header>
        <h1>Counterfoil</h1>
        <p>
          What the AI transaction agent tried to do with the money, and what reached Braintree.
          {data && ` ${data.runs.length} runs, exported ${data.asOf.slice(0, 16).replace('T', ' ')} UTC.`}
        </p>
        <nav>
          {counterfoilReport.pages.map((p) => (
            <button key={p.id} className={p.id === pageId ? 'active' : ''} onClick={() => openPage(p.id)}>
              {PAGE_TITLES[p.id] ?? p.id}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {error && <p className="message">Could not load counterfoil-data.json ({error}). Run scripts/export_dashboard.py first.</p>}
        {!error && !studioData && <p className="message">Loading…</p>}
        {studioData && (
          <AgStudioProvider licenseKey={LICENSE_KEY}>
            <AgStudio
              style={{ height: '100%', width: '100%' }}
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
    </>
  );
}
