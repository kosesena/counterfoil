# Counterfoil — submission copy

Reviewed 3 November 2026. Packaged on GitHub; not submitted to Devpost or published on YouTube. Resolve the two link checks below before pasting the final entry.

## Project name
Counterfoil

## Short description
Counterfoil is a deterministic guardrail for agentic commerce: a merchant on PayPal can give refunds to an AI agent, each one is checked against the store's records before Braintree moves money, and exceptions wait for a person.

## Links
- Interactive demo: https://counterfoil-demo.onrender.com
- Evidence dashboard: https://counterfoil-dashboard.vercel.app
- Source: https://github.com/kosesena/counterfoil — PUBLICATION PENDING. The complete source and assets must be public with the MIT license visible before submission. Private reviewer invitations do not satisfy this requirement.
- Video: YOUTUBE URL PENDING. After owner review, upload counterfoil-demo-eve-captioned.mp4 to YouTube, make it publicly visible, and insert its URL here and in the submission form.

## Inspiration
A small store takes PayPal. Returns arrive by e-mail, and the store wants an AI agent to handle them, because PayPal's Agent Toolkit already gives an agent a `create_refund` tool. But that e-mail is written by the customer, or by someone pretending to be one. PayPal can tell whether a refund is valid for the transaction. Only the store knows whether it is owed. We built the piece that lets a merchant on PayPal hand returns to an agent without handing over that decision.

## What it does
**Counterfoil lets a merchant on PayPal give refunds to an AI agent, and refunds only what came back.** A Reader extracts structured fields from an email without payment tools. A Runner uses those fields without seeing the original email. Counterfoil checks every payment request against trusted store records and returns PASS, APPROVAL or BLOCK.

The checks cover order ownership, remaining refund entitlement, reservations, item prices and quantities, provider line items and disputes. Held requests require a manager's decision. Approvals are bound to the exact request, expire and cannot be reused.

HOMI, a fictional homeware store, makes the flow visible. The live website replays recorded agent calls, compares no gate with a USD 200 cap and Counterfoil, and offers a separate Braintree sandbox checkout. The dashboard exposes measured outcomes and downloadable evidence.

## What the demo video shows
The main video includes a continuous, unsped-up 76-second recording of the deployed browser application captured on 3 November. It shows a USD 200 Braintree sandbox purchase, rejection of a USD 60 refund when only USD 40 remains available, a held USD 40 correction, manager approval, and the resulting sandbox refund. The captured evidence records zero refund calls before approval and one successful USD 40 refund afterward.

The agent calls in this flow are replayed from a saved run. Checkout, gate checks, approval and refund executed against the hosted application and Braintree sandbox during capture. The account is Braintree's mocked PayPal account, not a real PayPal wallet login. Browser automation acts as the manager. This is a working-product demonstration, not a new live-model evaluation or a human user study. English narration uses AssemblyAI’s stock Eve voice (aai-eve); it is synthetic, not a cloned speaker. English captions are burned into the image and supplied separately as an SRT file. Soft transitions appear between sections; the 76-second sandbox capture remains uninterrupted at its original speed.

## Why Braintree
The project's measured payment integration uses Braintree sandbox. The author could not obtain a PayPal account from Türkiye for this project; the PayPal REST adapter was therefore tested with simulated HTTP responses only. Braintree is explicitly included in the [official project requirements](https://paypalaihackathon.devpost.com/rules).

## How we built it
Python and FastAPI serve the demo. SQLite records refunds, reservations and charges in the gateway. Braintree sandbox integrations cover sales, refunds, voids, vaulted methods, line items, signed dispute webhooks and reconciliation sweeps. The MCP adapter accepts PayPal Agent Toolkit-shaped requests. The dashboard uses Next.js, React and AG Studio; the store uses Three.js and Blender assets.

The measured model experiments use a Reader/Runner split, paired Reader outputs and three gate conditions. The hosted live-AI option is configured for Claude Haiku 5.5. The recorded multi-model evaluations include nine models; coverage differs across development and holdout sets.

## Results
On the real Braintree sandbox (10–11 November; three local models, the 14 attacks, three repeats), wrong money moved in 59 of 126 attack runs without a gate, 59 of 126 with a USD 200 cap, and 0 of 126 with Counterfoil. That run has attacks only.

In the October simulation cohort, harmful outcomes occurred in 99 of 270 completed attack runs without a gate, 100 of 270 with a USD 200 cap, and 0 of 270 with Counterfoil. Harm includes wrong money movement or another customer's data being read. These are runs per condition, not 270 independent attack designs.

Genuine requests were handled correctly in 150 of 183 Counterfoil runs. This comprises 102 completed requests and 48 appropriate human-review outcomes; it is not a 150-payment completion claim. November local attacks, hosted attacks, clean controls and repeats remain separate because their fixtures and denominators differ. The stopped hosted pilot is preserved with its unknown outcome.

On 3 November, all 12 approval/recovery scenarios passed against Braintree sandbox. Locally injected timeouts and interruptions before or after provider acceptance did not permit a second payment on retry. The offline suite passes 539 tests, with 2 skipped and 1 expected failure. The separately recorded 3 November coverage measurement is 94.74%; this video edit did not remeasure coverage.

## Challenges and lessons
A spending cap cannot determine whether a refund is owed. Braintree's card limits already stop some invalid refunds, so we distinguish provider refusals from gate protection. We also separate an agent being misled from harmful execution: refusing a harmless request is not a security success.

Recorded traces make failures inspectable. Unknown outcomes stay unknown until reconciled, rather than being counted as successful defenses.

## Limits and next steps
These are synthetic store fixtures and sandbox measurements, not production reliability guarantees. The demo keeps checkout sessions in memory: after restart, old IDs are rejected instead of resuming the checkout. Persistent production ledgers, durable request identity and an operator reconciliation workflow remain deployment work. The recovery experiment reopens SQLite and constructs a fresh gateway; it does not simulate a host power failure.

PayPal REST is tested with simulated HTTP responses, not measured on a real REST sandbox account. Next steps are independent external testers, more model/day repetitions, real merchant integrations and measured REST-sandbox execution.

## AI tools used
Claude Code and OpenAI Codex assisted implementation, scenarios, reviews and documentation under Sena Köse's direction. The product uses AI for Reader/Runner decisions; the payment gate itself is deterministic code. The delivery video combines synthetic English narration, deployed-UI screenshots and the continuous sandbox browser capture described above. It does not present replayed agent calls as a new live-model run.

## Built with
Python, FastAPI, SQLite, Braintree, PayPal Agent Toolkit-shaped MCP, Claude, Ollama, Astropods, Next.js, React, TypeScript, AG Studio, Three.js, Blender, Render, Vercel, pytest.

## Testing instructions
Open https://counterfoil-demo.onrender.com and choose “Watch a recorded run”, P6-01, then “Compare the three checks”. This route is saved evidence and needs no account or model key. For the working payment path, use “Complete the test with PayPal”, create a sandbox purchase, run the Counterfoil refund path, inspect the held USD 40 correction and approve it. Only sandbox funds are involved. “Try live AI” is a separate mode that makes fresh model calls.

The current hosted service limits relevant checkout/live actions to 6 per client per 10 minutes and has a daily model budget. If a limit is reached, follow the displayed retry guidance; do not blindly retry an uncertain payment. Local setup and model/sandbox configuration are documented in demo/README.md. The public repository and a usable, free judge testing path must remain available through the end of judging, 15 December 2026 at 08:00 Pacific time. See REVIEW-BEFORE-PUBLISHING.md for the access check still required before release.

Official requirements verified 3 November 2026: [rules](https://paypalaihackathon.devpost.com/rules), [schedule](https://paypalaihackathon.devpost.com/details/dates).
