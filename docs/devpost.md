# Devpost submission: Counterfoil

Ready-to-paste answers for the PayPal AI Hackathon form, updated 3 Nov 2026. Every figure comes from `results/*.jsonl`
or from [`arastirma/kaynaklar.md`](arastirma/kaynaklar.md). The dashboard keeps the October multi-model results and
November follow-up cohorts separate. This file is a draft; it does not confirm submission or publication.

---

## Project name

Counterfoil

## Elevator pitch (≤ 200 characters)

> Across 9 AI models and 270 attack runs, a returns agent moved wrong money 99 times with no gate and 100 times behind a $200 cap. Behind Counterfoil: 0.

(151 characters. Source: `results/2026-10-25-*-r3-*.jsonl` and `results/2026-10-26-dev-r3-current-gate-*.jsonl`,
re-scored with the current scorer on 5 Nov: none 99/270, cap 100/270, counterfoil 0/270.)

Earlier pitch, kept as the README tagline: *An AI agent can be talked into a refund. A store's records can't.
Counterfoil checks every agent refund against the return record before Braintree moves the money.*

## Try it out

- Live demo (Braintree sandbox, live Claude, 3D store): https://counterfoil-demo.onrender.com
- Results dashboard: https://counterfoil-dashboard.vercel.app
- Code (MIT): https://github.com/kosesena/counterfoil
- Video: *(YouTube link, to add)*

## Built with

paypal, braintree, braintree-python-sdk, paypal-agent-toolkit, mcp, claude, anthropic-api, openai-python, ollama, astropods, ag-grid, ag-studio, render, vercel, python, fastapi, sqlite, pytest, next.js, react, typescript, three.js, blender, meshy

---

## About the project

*(paste everything from here to the end of "What's next")*

### Inspiration

Stores are starting to let AI agents answer customer e-mail, and PayPal's own Agent Toolkit already gives an agent a `create_refund` tool. But the e-mail is written by the customer, or by whoever pretends to be one. OWASP ranks prompt injection first among LLM risks (LLM01:2025), including instructions hidden in e-mails and attachments, and *Moffatt v. Air Canada* (2024) held a business responsible for what its AI told a customer. Return fraud is already large without agents: US retailers lost an estimated $103B to fraudulent returns and claims in 2024 (Appriss Retail and Deloitte).

Support bots are already being talked into promises they shouldn't make. In a red-team test of 14 live support chatbots, Reinforce Labs reported that 11 made unapproved commitments such as refunds or warranties (1 Oct 2026; the firm's own account, companies unnamed). A UK shop owner reported that the after-hours bot was flattered into inventing discount codes up to 80% off (Feb 2026, the owner's account). We found no verified case yet of an agent that *moved* money this way, because most bots could only promise. That is changing: PayPal's Agent Toolkit gives an agent `create_refund`, and support agents that can issue refunds are spreading. Counterfoil is meant to be in place before the promise becomes a payment.

**Who it's for.** Merchants who let an AI support agent issue refunds, and that is a feature you can switch on today: Intercom's Fin ships "Create Shopify Refund" and Stripe refund actions, Gorgias's AI Agent refunds the shopper when it cancels an order or removes an item, and PayPal's Agent Toolkit gives an agent `create_refund`. Those merchants already fight return abuse by hand: on the Shopify Community one raised the restocking fee to 20% on every order after 18 near-identical return requests for cheap items; another is told to switch the returns portal to "manual approval only". Counterfoil does that check against the return record for the agent, on every call, and leaves a person only what doesn't match. Sources and their limits: [public evidence](https://github.com/kosesena/counterfoil/blob/main/docs/arastirma/2026-11-02-public-evidence.md).

Our first Braintree sandbox experiment showed where the gap is. Braintree refuses a card refund above the sale total. It cannot know whether the customer sent back one cup or four, whether the sender owns the order, or that USD 60 of this return was already refunded yesterday. Only the store knows that. Counterfoil sits in that gap.

Built solo from Türkiye, where PayPal accounts can't be opened, on **Braintree, the PayPal service PayPal's team confirmed for this hackathon**.

### What it does

**Counterfoil refunds only what came back.** It is a gate between an AI returns agent and the payment rail:

1. **Reader** (an AI agent with no tools) reads the customer's e-mail and hands off fixed fields: order, return record, request, amount, items.
2. **Runner** (an AI agent that never sees the e-mail) asks to `refund`, `charge`, `void` or `lookup_transaction`.
3. **Counterfoil** holds the only Braintree keys and answers every call with **PASS**, **APPROVAL** (held for the store manager) or **BLOCK**, by comparing it with the store's own records: who owns the order, what the return record (RMA) still allows after earlier and reserved refunds, catalog price × quantity for a charge, Braintree's own line items for the sale, and open chargebacks.
4. **Braintree** moves only what passed, or what a person approved. Each approval is single-use and bound to the exact call the manager saw.

The agent can still be fooled; Counterfoil makes sure a fooled agent can't send the money.

### Try it in 90 seconds

1. Open the **live demo**, pick **"Nella asks for more"** (attack P6-01, a split refund) and press **Compare the three checks**. With no gate and with a $200 cap, USD 60 reaches the rail. With Counterfoil, no money moves.
2. Press **Watch it in the store ↑**: the six felt characters replay the run in a 3D HOMI store, one step per click: Nella's note, Reader's hand-off, Runner's call, Counterfoil's BLOCK with its reason, what reached PayPal / Braintree, and what would have left without the gate.
3. Switch to **Live AI** and **Write your own** attack: Claude Haiku 5.5 reads it live and Counterfoil decides (rate-limited, test money only).
4. **Pay with PayPal (sandbox)** for the scenario's order, then let the recorded agent refund it through the gate: real Braintree sandbox transactions.
5. Open the **dashboard** for every number below, broken down by model.

### Why Braintree, and not the PayPal REST API

[PayPal's Türkiye notice](https://www.paypal.com/tr/home?locale.x=en_TR) states that local operations stopped in June 2016. The author could not obtain a PayPal account for this project, so the PayPal REST path was not exercised against a real REST sandbox. The [official hackathon rules](https://paypalaihackathon.devpost.com/rules) explicitly include Braintree as a qualifying PayPal service. So instead we built on the **Braintree sandbox** with Braintree's mocked PayPal account, used Braintree well beyond a checkout (below), and **kept PayPal's agent interface**: our MCP server offers the Agent Toolkit's `create_refund` unchanged for the agent, and a gated PayPal REST rail stands behind the Toolkit's `create_refund`, ready for a PayPal account. That rail is the one path we could not run for real; it is tested with a faked HTTP layer.

### How we built it

**PayPal and Braintree, used in depth (all sandbox):**
- `transaction.sale` with **line items** (product code, quantity, amounts) and the **mocked PayPal account** nonce, PayPal checkout through Braintree Drop-in, vaulted PayPal methods for reorders, `transaction.refund`, `transaction.void`, `transaction.find`.
- `transaction_line_item.find_all`: before a refund, the gate checks the return record against what Braintree says was sold, a second source next to the store's own records.
- `api_request_key` derived from the money movement, so a retried or raced refund pays once (checked in the sandbox).
- **Disputes**: a refund on a transaction with an open chargeback is blocked; Braintree itself pays it, which we showed on the dispute test card.
- **Signed webhooks**: a `dispute_opened` notification locks refunds on that transaction before the next agent call, even one already waiting for the manager.
- `transaction.search` **refund sweep**: finds refunds made behind the gate's back, in the Control Panel or by another tool.
- **PayPal Agent Toolkit-shaped MCP server** (`counterfoil-mcp`): Claude Desktop, Cursor or Claude Code call `create_refund(capture_id, amount)` exactly as with the Toolkit, and every call goes through the gate to the Braintree sandbox.

**AI, used in depth:**
- Two agents with split duties (Reader without tools, Runner without the e-mail) over an OpenAI-compatible client.
- **Nine models measured**: four local (qwen2.5, qwen3, llama3.1, hermes3 on Ollama) and five cloud (Claude Haiku 4.5, Sonnet 5, Opus 5.5; GPT-5.6 Sol and Terra) through the **Astropods** Astro AI Gateway.
- **Live Claude Haiku 5.5** in the hosted demo, with per-visitor rate limits and a daily call budget.
- **AG Studio** (AG Grid) dashboard over every run, with a review desk that explains each held call. Its case panel runs on rules over the recorded data, not on an LLM.

**Engineering:** Python, FastAPI and SQLite (orders, RMAs, refund reservations, charge states); **533 passing tests**,
2 skipped and 1 expected failure, **94.74% coverage** (3 Nov 2026), without an LLM or network; 10 architecture decision
records; the demo configured on **Render Starter**, the dashboard on Vercel. Mutation results remain dated to their
24 Oct run; see [quality evidence](quality.md).

### The results

The table below is the **October multi-model experiment**. November experiments are separate in the dashboard:
30 blind attacker cases on the local rail, a repaired 30-run hosted attack cohort, 36 clean-control sandbox runs,
and 12 repeated executions. The original six-run hosted pilot remains archived with one unknown outcome.
These datasets have different fixtures and denominators and are not pooled into the table below.

In the repeated clean cohort, Counterfoil completed both valid refunds and held both USD 120 reorders for human
confirmation; no gate and the USD 200 cap each charged both reorders without that confirmation. Reader outputs
were cached and identical across repeats, so this is not independent end-to-end sampling. Detailed protocols,
limits and downloadable scored rows accompany each experiment on the dashboard.

22 scenarios: 14 attacks in 7 families and 8 genuine requests, split into a dev set and a holdout set kept apart while the gate was written. The evaluation spans nine models, three repeats and three conditions with paired Reader hand-offs. Model coverage differs between dev and holdout; the table reports completed runs per condition, not a full Cartesian product of every model and scenario.

| | No gate | $200 cap | Counterfoil |
|---|:---:|:---:|:---:|
| **Wrong money moved** (or another customer's data read), attack runs | 99/270 | 100/270 | **0/270** |
| Agent misled, attack runs | 141/270 | 142/270 | 139/270 |
| Genuine requests handled right | 102/183 | 123/183 | **150/183 (82%)** |
| Real Braintree sandbox (qwen2.5, dev set) | 4/7 | 4/7 | **0/7** |
| Worst case: Reader and agent fully on the attacker's side, no model | 11/14 | 11/14 | **0/14** |

The agent is misled about equally often in every condition; only the money changes. The $200 cap stopped nothing: every harmful call was below it.

### What ran on a real rail, and what didn't

- **Real Braintree sandbox:** the sandbox evaluation run, the worst case, the live demo (checkout, refunds, voids, dispute card, webhooks) and the MCP server run.
- **In-memory rail with the sandbox's card limits:** the 270 runs, so nine models × three repeats cost no sandbox noise. Real models decided every one of them.
- **Not run against PayPal REST:** the Toolkit path (`toolkit.py` → `paypal.py`) is tested with a faked HTTP layer only, because no PayPal account can be opened from Türkiye.
- **Mocked PayPal inside Braintree** does not enforce the refund total; no stop that only this gap explains is counted for Counterfoil.

### Design

HOMI is a small homeware store made of felt. Six characters carry the story: Nella the customer, Reader, Runner, Counterfoil (a plum gatekeeper in a beret), the store manager and the PayPal terminal. They appear as felt portraits on the dashboard and as **Meshy** 3D models in a **Blender** store in the live demo, where they replay each test step by step. Nothing plays on its own; every step is a click. The dashboard explains the system in plain words first and keeps the evidence one click away: the results band, a comparison with the alternatives, the review desk for held calls and every recorded agent call.

### What's new here

Guards for agent payments sit on the **buyer's** side: an agent spends for a customer, and the guard limits how much and where (caps, allowlists, signed intent, approval over a threshold). A returns agent works on the **seller's** side, giving the store's money back, and the question there is different: *is this money owed?* A cap can't tell a USD 60 refund that is owed from one that isn't; it moved wrong money in 100 of 270 runs. Counterfoil answers with the store's return record and Braintree's own line items, and leaves to Braintree what Braintree already refuses.

### Challenges we ran into

- **Braintree changed the design.** Our first attack, a refund above the order total, is something Braintree already refuses on cards, so it couldn't be our selling point. We rebuilt the gate around the return record, which only the merchant has.
- **Mocked PayPal is too permissive.** It accepted refunds above the sale total. We never count that as a Counterfoil catch.
- **Honest scoring.** An injection the model ignores is not a gate success, and a blocked read is not a leak. Separating "agent misled" from "harm" is what makes the zero mean something.
- **Our own runs found bugs in the gate.** An earlier gate let qwen3 push an inflated reorder through in all three repeats; that led to the rule that every charge is confirmed by a person. Each fix came with a test.

### Accomplishments that we're proud of

- **Zero wrong money across nine models and 270 attack runs**, while completing the same genuine requests as no gate (102 of 183) and handling 82% right overall.
- **Attacks that pass both baselines**: over-refunds, split refunds and replays stay below the sale total, so neither Braintree nor a cap stops them.
- **A chargeback locks refunds before the agent asks**, through Braintree's own webhook.
- **One config entry** puts the gate in front of any MCP client that speaks the Toolkit's `create_refund`.

### What we learned

- **Payment rails protect the transaction, not the business rule.** The gap is the merchant's to close, with the merchant's own records, not with smarter prompts.
- **Better models are fooled less often, not never.** With no gate, Claude Sonnet 5 was misled in 5 of 21 dev attack runs, qwen2.5 in 12, llama3.1 in 18.
- **Measure attempts and harm separately**, or a model that ignores an injection looks like a gate success.

### What's next

- **PayPal REST, measured**: run the Toolkit path against a real PayPal REST sandbox.
- **More evidence**: attacks written by people outside the project, more repeats on other days, more models.
- **A store's own settings**: refund window, automatic limit and who approves, editable by the merchant.
- **Privacy in a real store (KVKK / GDPR)**: tell customers an AI agent reads their e-mail and staff review held calls, which also answers the right to object to purely automated decisions.

---

## AI tools used (form question)

- **In the product:** Claude Haiku 5.5 reads e-mails and drives the agent in the live demo (Anthropic API); the nine evaluated models above ran through Ollama and the Astropods Astro AI Gateway. The dashboard's case panel is rule-based, not an LLM.
- **To build it:** Claude Code wrote most of the code (gate, rails, agents, evaluation, dashboard, demo, 3D scenes) under Sena Köse's design and decisions; OpenAI Codex wrote the scenario texts, designed HOMI's felt look and reviewed the code, and every review finding was fixed with a test; Meshy generated the 3D characters; image models made the felt portraits.

## New project (form question, if asked)

Counterfoil was started from scratch for this hackathon: the first commit is 23 Oct 2026 (`e2f6393`). It builds on the
author's graduation thesis topic (indirect prompt injection against LLM agents in ERP systems), but no code was carried over.

---

## Delivery package

The concise submission copy, judge walkthrough and narrated-video script are in [`submission/`](submission/README.md).
The package includes the 3 November approval/recovery results and keeps measured cohorts separate.

## Before pressing submit

- [ ] Repository public, MIT visible in the About section
- [ ] YouTube video public, under 3 minutes, link added above and in the form
- [ ] Live demo and dashboard open; verify `/healthz` and the Starter deployment before submission
- [ ] Screenshots: results band, comparison table, 3D store with a Counterfoil BLOCK badge, review desk
