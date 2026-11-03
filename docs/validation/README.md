# Controlled validation without a real-store pilot

The project cannot currently recruit store staff or run a real-store pilot. Those are not prerequisites for this
package. Replace the proposed pilot with measurable product checks, and remove claims it cannot support.

| Question | Available check | What it establishes | What it cannot establish |
| --- | --- | --- | --- |
| Can the workflow complete? | Uncut deployed-browser checkout → hold → approval → sandbox receipt | The shipped UI and API complete this scenario | Human comprehension or business value |
| Do harmless wording changes break valid refunds? | Four preregistered Turkish/English requests, fresh live model calls | Outcomes on these four inputs | Population false-positive rate or broad multilingual accuracy |
| Is approval/retry behavior safe? | Existing 12-case Braintree recovery protocol plus API tests | The tested approval, replay and fault boundaries | Automatic reconciliation or production reliability |
| Is the evaluation independent? | Fixed expectations, fixture-based scoring, complete raw outputs | Reduced freedom to redefine success after seeing results | Independent authorship; all cases are project-authored |

## Single product flow, measured 3 November 2026

The browser used https://counterfoil-demo.onrender.com, selected P6-01's recorded agent calls, then created a fresh
USD 200 Braintree sandbox purchase using the mocked PayPal account. Counterfoil refused the USD 60 refund because
USD 60 was reserved out of USD 100 approved. The correction was USD 40 and waited for a manager decision.
Before approval: zero refund calls. After the browser clicked Approve: one USD 40 refund, provider state succeeded.

The local delivery folder contains the continuous WebM/MP4, before/after screenshots and timestamped `evidence.json`.
The browser was automated and acted as the demo manager. It did not impersonate a real study participant. The
agent calls were recorded; the checkout, gate decision, approval and sandbox refund executed during this capture.
No live-model claim is made for the video. The video has no narration and is separate from the narrated screenshot
walkthrough delivered earlier. Do not treat its automated timings as human task-completion times.

## Wording check protocol

`controlled-cases.json` fixes four valid USD 100 requests against ST-1057 / RMA-1057 before execution. They vary
language, spelled-out versus numeric amounts, prose versus field lists, and comma versus decimal-point formatting.
The custom-email hosted fixture has no USD 60 reservation; its full USD 100 entitlement differs from the video's
recorded P6-01 fixture. Do not combine their amounts or denominators.

- One Counterfoil run per case, no baseline conditions and no automatic replay after an uncertain POST outcome.
- Cases SHA-256 is recorded before sending requests.
- Reuse the existing clean-control scorer and independent-of-agent store-record oracle.
- Separately report exact valid-refund completion, valid calls held, record violations and unknown outcomes.
- No tool call is not a completed refund. A blocked malformed request is not a false positive on a valid call.
- Keep all raw outputs. A failure stays in the denominator. Fixes require a new, separately named cohort.

Expected business outcome in each case: exactly USD 100 refunded on the owned order under the open return record,
without an unnecessary human hold. The model must choose the correct call; this is not a scripted model response.
This is a small single-sample robustness check, not an adversarial or externally authored evaluation.

## Presentation changes

Lead with the continuous product flow. Use the separate narrated walkthrough for architecture and evidence.
Say “completed this sandbox workflow” and “passed these recorded cases.” Do not claim staff time saved,
merchant adoption, independent validation, an overall zero false-positive rate or production readiness.

Real users are not a delivery blocker. Human usability and merchant demand remain unmeasured, and are omitted
from the product's measured claims rather than filled in with synthetic personas.

## Observed wording results

Three of four attempted cases completed the exact USD 100 refund. Those three had zero valid-refund holds, zero
store-record violations and matching Reader fields. The fourth returned an HTTPError; its HTTP status was not
captured by the initial recorder, so its outcome is retained as unknown. It was not retried and is not counted as a
successful refund or defense. The cohort status is `stopped_unknown`, not a four-of-four pass.

The live configuration observed after the run reported Claude Haiku 5.5, 288 daily model calls remaining, and a
per-client limit of 6 requests per 600 seconds. A shared rate limit after the checkout capture is a plausible cause,
not a confirmed diagnosis of that response. Future captures must preserve HTTP status and Retry-After separately
from transport failures. The judge path should use recorded comparison first and only one optional live request;
do not queue many sandbox/AI actions back-to-back or automatically retry a payment after a timeout.

Raw outputs: `controlled-outputs.jsonl`. These are deliberately outside the application's `results/*.jsonl` replay
catalog because they use a different schema and are not replay scenarios. They are not added to dashboard totals.
