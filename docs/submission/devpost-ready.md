# Counterfoil — submission copy

Prepared 3 November 2026. This is submission material, not a submitted entry.

## Project name
Counterfoil

## Short description
Counterfoil checks AI-requested refunds against merchant records before Braintree moves money, and holds exceptions for human review.

## Links
- Interactive demo: https://counterfoil-demo.onrender.com
- Evidence dashboard: https://counterfoil-dashboard.vercel.app
- Source: https://github.com/kosesena/counterfoil — currently private; reviewer access must be arranged.
- Video: upload the accompanying MP4, then paste its shareable URL into the form.

## Inspiration
An AI returns agent can read a convincing email and ask for the wrong refund. A payment provider knows the sale total, but not which items came back or how much the store's return record still allows. We built Counterfoil to check that merchant evidence before an agent's request reaches the payment provider.

## What it does
A Reader extracts structured fields from an email without payment tools. A Runner uses those fields without seeing the original email. Counterfoil checks every payment request against trusted store records and returns PASS, APPROVAL or BLOCK.

The checks cover order ownership, remaining refund entitlement, reservations, item prices and quantities, provider line items and disputes. Held requests require a manager's decision. Approvals are bound to the exact request, expire and cannot be reused.

HOMI, a fictional felt homeware store, makes the flow visible. The live website replays recorded agent calls, compares no gate with a USD 200 cap and Counterfoil, and offers a separate Braintree sandbox checkout. The dashboard exposes measured outcomes and downloadable evidence.

## How we built it
Python and FastAPI serve the demo. SQLite records refunds, reservations and charges in the gateway. Braintree sandbox integrations cover sales, refunds, voids, vaulted methods, line items, signed dispute webhooks and reconciliation sweeps. The MCP adapter accepts PayPal Agent Toolkit-shaped requests. The dashboard uses Next.js, React and AG Studio; the store uses Three.js and Blender assets.

The measured model experiments use a Reader/Runner split, paired Reader outputs and three gate conditions. The hosted live-AI option is configured for Claude Haiku 5.5. The recorded multi-model evaluations include nine models; coverage differs across development and holdout sets.

## Results
In the October simulation cohort, harmful outcomes occurred in 99 of 270 completed attack runs without a gate, 100 of 270 with a USD 200 cap, and 0 of 270 with Counterfoil. Harm includes wrong money movement or another customer's data being read. These are runs per condition, not 270 independent attack designs.

Genuine requests were handled correctly in 150 of 183 Counterfoil runs. That includes appropriate holds or abstentions; it is not a 150-payment completion claim. November local attacks, hosted attacks, clean controls and repeats remain separate because their fixtures and denominators differ. The stopped hosted pilot is preserved with its unknown outcome.

On 3 November, all 12 approval/recovery scenarios passed against Braintree sandbox. Locally injected timeouts and interruptions before or after provider acceptance did not permit a second payment on retry. The offline suite passes 533 tests, with 2 skipped and 1 expected failure, at 94.74% coverage.

## Challenges and lessons
A spending cap cannot determine whether a refund is owed. Braintree's card limits already stop some invalid refunds, so we distinguish provider refusals from gate protection. We also separate an agent being misled from harmful execution: refusing a harmless request is not a security success.

Recorded traces make failures inspectable. Unknown outcomes stay unknown until reconciled, rather than being counted as successful defenses.

## Limits and next steps
These are synthetic store fixtures and sandbox measurements, not production reliability guarantees. The demo keeps checkout sessions in memory: after restart, old IDs are rejected instead of resuming the checkout. Persistent production ledgers, durable request identity and an operator reconciliation workflow remain deployment work. The recovery experiment reopens SQLite and constructs a fresh gateway; it does not simulate a host power failure.

PayPal REST is tested with simulated HTTP responses, not measured on a real REST sandbox account. Next steps are independent external testers, more model/day repetitions, real merchant integrations and measured REST-sandbox execution.

## AI tools used
Claude Code and OpenAI Codex assisted implementation, scenarios, reviews and documentation under Sena Köse's direction. Model-generated artwork and Meshy assets support the felt-store presentation. The product uses AI for Reader/Runner decisions; the payment gate itself is deterministic code. The delivery video uses synthetic English narration and screenshots of the deployed application, not a new live model run.

## Built with
Python, FastAPI, SQLite, Braintree, PayPal Agent Toolkit-shaped MCP, Claude, Ollama, Astropods, Next.js, React, TypeScript, AG Studio, Three.js, Blender, Meshy, Render, Vercel, pytest.
