import { StoryContinuation } from './story-continuation';
import type { CounterfoilData } from './studio-data';

export function ReviewIntro({ data, onContinue }: { data: CounterfoilData; onContinue: () => void }) {
  const runIds = new Set(data.runs.filter(run => run.condition === 'Counterfoil').map(run => run.id));
  const calls = data.calls.filter(call => call.moneyCall === 1 && runIds.has(call.runId));
  const held = calls.filter(call => call.decision === 'APPROVAL').length;
  const blocked = calls.filter(call => call.decision === 'BLOCK').length;
  return <section className="review-intro" aria-labelledby="review-title">
    <div className="review-copy">
      <span className="review-eyebrow">COUNTERFOIL / THE REVIEW DESK</span>
      <h1 id="review-title">Why is this<br/><em>request waiting?</em></h1>
      <p>See what the agent asked for, what the store allows, and why Counterfoil stepped in.</p>
      <div className="review-actions"><a href="https://counterfoil-demo.onrender.com" target="_blank" rel="noopener">Try an approval in the sandbox ↗</a></div>
      <small>Illustrated story · recorded cases in Technical details</small>
    </div>
    <figure className="review-manager">
      <img src="crew/manager-review-v1.png" alt="Store manager examining a held request on a tablet" width="1127" height="1400"/>
      <figcaption><strong>“I check before I decide.”</strong><span>The store manager · human review</span></figcaption>
    </figure>
    <div className="review-simple"><StoryContinuation view="review" onContinue={onContinue} /></div>
    <details className="review-simple simple-disclosure"><summary>Snapshot counts · {held} held, {blocked} blocked</summary><p>Recorded evaluation calls across models, simulation and sandbox. These count calls, not distinct customers or test runs. This is not a live queue.</p></details>
  </section>;
}
