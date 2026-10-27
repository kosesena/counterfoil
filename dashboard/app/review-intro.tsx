import type { CounterfoilData } from './studio-data';

export function ReviewIntro({ data }: { data: CounterfoilData }) {
  const runIds = new Set(data.runs.filter(run => run.condition === 'Counterfoil').map(run => run.id));
  const calls = data.calls.filter(call => call.moneyCall === 1 && runIds.has(call.runId));
  const held = calls.filter(call => call.decision === 'APPROVAL').length;
  const blocked = calls.filter(call => call.decision === 'BLOCK').length;
  return <section className="review-intro" aria-labelledby="review-title">
    <div className="review-copy">
      <span className="review-eyebrow">COUNTERFOIL / THE REVIEW DESK</span>
      <h1 id="review-title">A pause.<br/><em>A closer look.</em></h1>
      <p>See what the agent asked for, what the store allows, and why Counterfoil stepped in.</p>
      <div className="review-actions"><a href="#review-workspace">Inspect the records ↓</a><a href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">Try an approval in the sandbox ↗</a></div>
      <small>Recorded evaluation calls · read-only · no real funds</small>
    </div>
    <figure className="review-manager">
      <img src="crew/manager-review-v1.png" alt="Store manager examining a held request on a tablet" width="1127" height="1400"/>
      <figcaption><strong>“I check before I decide.”</strong><span>The store manager · human review</span></figcaption>
    </figure>
    <div className="review-decisions" aria-label="Recorded Counterfoil decisions">
      <article className="review-held"><span>APPROVAL</span><h2>{held} held calls</h2><p>The exact request waits for a person to review. Holding a call is not permission to pay.</p></article>
      <article className="review-blocked"><span>BLOCK</span><h2>{blocked} blocked calls</h2><p>This call cannot be approved. Resolve the cause and submit a new request for another check.</p></article>
      <p className="review-scope">Full Counterfoil snapshot across all models, simulation and sandbox runs. These are recorded calls, not today’s pending queue; counts here stay fixed while the records below can be filtered.</p>
    </div>
    <ol className="review-guide" aria-label="How to inspect a case"><li><b>01 / Choose</b><span>Filter the condition, decision and model.</span></li><li><b>02 / Compare</b><span>Read the store allowance, Reader hand-off and agent request.</span></li><li><b>03 / Understand</b><span>Inspect the failed checks and what can happen next.</span></li></ol>
  </section>;
}
