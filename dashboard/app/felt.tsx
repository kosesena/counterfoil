'use client';

// The felt sections of the Overview (Codex's design, 25 Oct): the hero with Counterfoil and the receipt, the result band,
// the return crew, the story section around the 3D player, and the closing band. The mascots are Codex's needle-felt
// renders on cream (public/crew/); the page multiplies them onto its own cream, so their backdrop disappears.

import { useEffect, useRef } from 'react';

const DEMO = 'https://counterfoil-demo.gloveson.space';

// Counterfoil leans towards the pointer on desktop: a turn, a tilt and a small step, eased by CSS. Nothing moves on
// touch screens or with reduced motion.
export function FollowingFoil({ src, alt }: { src: string; alt: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!fine.matches || calm.matches) return;
    let raf = 0;
    const onMove = (e: PointerEvent) => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const r = el.getBoundingClientRect();
        const dx = (e.clientX - (r.left + r.width / 2)) / window.innerWidth;
        const dy = (e.clientY - (r.top + r.height * 0.35)) / window.innerHeight;
        const near = Math.hypot(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2)) < r.width * 0.9;
        el.style.setProperty('--turn', `${Math.max(-1, Math.min(1, dx * 2)) * 14}deg`);
        el.style.setProperty('--tilt', `${Math.max(-1, Math.min(1, dx * 2)) * 4}deg`);
        el.style.setProperty('--nod', `${Math.max(-1, Math.min(1, dy * 2)) * -6}deg`);
        el.style.setProperty('--step', `${Math.max(-1, Math.min(1, dx * 2)) * 10}px`);
        el.classList.toggle('near', near);
      });
    };
    const reset = () => { for (const k of ['--turn', '--tilt', '--nod', '--step']) el.style.removeProperty(k); el.classList.remove('near'); };
    window.addEventListener('pointermove', onMove);
    document.addEventListener('pointerleave', reset);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('pointermove', onMove); document.removeEventListener('pointerleave', reset); };
  }, []);
  return (
    <div className="foil" ref={ref}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} draggable={false} />
    </div>
  );
}

export function Hero({ onStory }: { onStory: () => void }) {
  return (
    <section className="f-hero">
      <div className="f-hero-copy">
        <span className="f-kicker">Counterfoil / returns control</span>
        <h1>A little trust.<br />A firm boundary.</h1>
        <p>Let agents handle returns. Keep money inside the rules.</p>
        <div className="f-actions">
          {/* Codex's felt buttons (docs/gorseller/site-tasarim/buttons-v1/) */}
          <button className="f-patch" onClick={onStory}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="buttons/watch-the-story.webp" alt="Watch the story" />
          </button>
          <a className="f-patch" href={DEMO} target="_blank" rel="noopener">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="buttons/try-it-live-cream.webp" alt="Try it live" />
          </a>
        </div>
      </div>
      <div className="f-hero-art">
        <FollowingFoil src="crew/counterfoil.webp" alt="Counterfoil, HOMI's felt gatekeeper, with a ledger under his arm" />
        <div className="f-receipt" aria-label="The agent asked for 60 USD; Counterfoil blocked it; 40 USD is still owed">
          <b>$60</b><span>requested</span>
          <i />
          <em>Blocked</em>
          <i />
          <b>$40</b><span>remaining</span>
        </div>
      </div>
    </section>
  );
}

export function ResultBand({ compare, runs, models }: { compare: { label: string; harm: number; total: number }[]; runs: number; models: number }) {
  return (
    <section className="f-band felt">
      {compare.map((c) => (
        <div key={c.label} className={c.label === 'Counterfoil' ? 'win' : ''}>
          <span>{c.label}</span>
          <strong>{c.harm}<small>/{c.total}</small></strong>
        </div>
      ))}
      <p>Attack runs where wrong money reached Braintree · {runs} runs, {models} models</p>
    </section>
  );
}

const CREW = [
  { img: 'crew/reader.webp', name: 'Reader', title: 'Reads the note', text: 'Pulls the order, the return and the amount out of what the customer wrote.' },
  { img: 'crew/runner.webp', name: 'Runner', title: 'Requests the refund', text: 'Turns the note into a money call: refund, charge or void.' },
  { img: 'crew/counterfoil-checking.webp', name: 'Counterfoil', title: 'Checks the rules', text: "Compares every call with the store's own records before it leaves." },
];

export function Crew() {
  return (
    <section className="f-crew">
      <h2>Meet the return crew.</h2>
      <p className="f-sub">Two AI agents and one gate. Different skills, a safer outcome.</p>
      <ol>
        {CREW.map((c) => (
          <li key={c.name}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={c.img} alt={c.name} draggable={false} />
            <b>{c.title}</b>
            <span>{c.text}</span>
          </li>
        ))}
        <li className="rail">
          <div className="f-rail felt"><b>Braintree</b><i /><i /></div>
          <b>Moves the money</b>
          <span>Only what Counterfoil lets through reaches the sandbox: refunds, sales and voids.</span>
        </li>
      </ol>
    </section>
  );
}

export function StoryAside() {
  const open = () => window.dispatchEvent(new CustomEvent('homi:story-go', { detail: 2 }));
  return (
    <aside className="f-aside felt">
      <h3>A real sandbox checkout, opened from this session.</h3>
      <p>Step 2 shows a QR code for your visit. Scan it and HOMI&apos;s receipt is paid with PayPal in the Braintree sandbox; the story then refunds that same sale.</p>
      <button className="f-patch" onClick={open}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="buttons/open-checkout.webp" alt="Open checkout" />
      </button>
    </aside>
  );
}

export function ClosingBand() {
  return (
    <section className="f-close">
      <div>
        <h2>See where the boundary holds.</h2>
        <p>Try the interactive demo with real return flows in the Braintree sandbox.</p>
      </div>
      <a className="f-patch" href={DEMO} target="_blank" rel="noopener">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="buttons/try-it-live-cream.webp" alt="Try it live" />
      </a>
    </section>
  );
}

// AG Studio draws the Condition filter as plain text buttons with no per-item hook. This tags each one with its
// condition so globals.css can swap in Codex's felt patches (buttons/cond-*.webp); the text stays for screen readers.
const CONDITIONS: Record<string, string> = { Counterfoil: 'counterfoil', '$200 cap': 'cap', 'No gate': 'none' };

export function useFeltConditions() {
  useEffect(() => {
    const tag = () => {
      for (const b of document.querySelectorAll<HTMLButtonElement>('.ag-studio-button-filter-widget-item:not([data-cond])')) {
        const id = CONDITIONS[b.textContent?.trim() ?? ''];
        if (id) b.dataset.cond = id;
      }
    };
    tag();
    const seen = new MutationObserver(tag);
    seen.observe(document.body, { childList: true, subtree: true });
    return () => seen.disconnect();
  }, []);
}
