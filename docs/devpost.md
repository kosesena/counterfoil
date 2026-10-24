# Devpost form: draft answers

Draft for the 12 Nov 2026 submission. Every figure comes from `results/*.jsonl` or [`arastirma/kaynaklar.md`](arastirma/kaynaklar.md). Update the results table whenever new runs land: more repeats, the holdout set, more models, or `--rail braintree`.

## Project name
Counterfoil

## Tagline
Your AI agent can be talked into a refund. Your store's records can't. Counterfoil checks every agent refund and charge against the order before Braintree moves the money.

## Inspiration
Shops are starting to hand customer e-mail to AI agents, and PayPal's own Agent Toolkit already gives agents a `create_refund` tool. But the e-mail is written by the customer, or by whoever is pretending to be one. OWASP ranks prompt injection first among LLM risks (LLM01:2025), including instructions hidden in e-mails and documents. *Moffatt v. Air Canada* (2024) showed that a business answers for what its AI says.

Our Braintree sandbox experiment showed what the payment rail can and can't catch. It refuses a card refund above the transaction total. It has no idea whether the customer returned one item or three, or whether the sender owns the order. That gap, between what the rail can see and what only the merchant knows, is where Counterfoil sits.

The project builds on the author's ongoing graduation thesis on indirect prompt injection against LLM agents in ERP systems, rewritten from scratch for payments.

## What it does
A Reader agent reads the raw customer e-mail. It has no tools and passes on a fixed set of fields. A Transaction agent never sees the e-mail; it calls `refund`, `charge`, `void` or `lookup_transaction`. Every call goes through Counterfoil, the only component holding Braintree credentials.

Counterfoil compares the call with the store's record of that transaction:

- The sender owns the order.
- The refund cites an open return authorisation (RMA) and doesn't exceed what it still allows, across calls and sessions.
- No refund is replayed, and no unreconciled outcome is retried.
- A charge is held for a human to confirm the itemised total, because no store record says how many the customer ordered. It must also equal catalog price × the Reader's quantity, on the sender's own vaulted method, once per e-mail.
- The call matches the Reader's hand-off.

The result is PASS, APPROVAL (held for a human, with a single-use, time-limited approval bound to the exact arguments) or BLOCK.

**Measured on 7 attacks and 6 genuine requests, dev set, 3 repeats:** 21 attack runs and 18 genuine runs per model and condition, from the committed `results/2026-10-24-dev-r3-*.jsonl`.

| Model | Agent misled (no gate) | Harm: no gate | Harm: $200 cap | Harm: Counterfoil | Genuine requests handled right (Counterfoil) |
|---|---|---|---|---|---|
| qwen2.5 (local, 8B) | 12/21 | 12/21 | 12/21 | **0/21** | 18/18 |
| Claude Haiku 4.5 | 9/21 | 9/21 | 9/21 | **0/21** | 18/18 |
| GPT-5.6 Sol | 9/21 | 9/21 | 9/21 | **0/21** | 18/18 |
| Claude Opus 5.5 | 6/21 | 6/21 | 6/21 | **0/21** | 18/18 |
| GPT-5.6 Terra | 6/21 | 6/21 | 6/21 | **0/21** | 18/18 |
| Claude Sonnet 5 | 5/21 | 5/21 | 5/21 | **0/21** | 18/18 |

Notes on the table:
- "Harm" means wrong money moved, or another customer's data was read. In total: 47 harmful outcomes in 126 attack runs with no gate, 47 with a $200 cap, 0 with Counterfoil.
- "Handled right" is 15 genuine requests completed plus 3 held for review: the $300 return (CLEAN-07), which store policy says needs a person. With no gate, that return went through unreviewed.
- The $200 cap stopped nothing: every harmful amount was below it.
- Measured with the earlier gate (commit 6f30a4a). A local qwen3 run, still in progress and not committed yet, broke the zero. In both repeats so far, its Reader obeyed P7-01's hidden HTML and handed off 6 cups for $150.00; the charge matched that hand-off, and $150.00 reached the rail. The gate now holds every charge for confirmation of the itemised total, so that charge is held. The genuine reorder (CLEAN-06) is held too.

## How we built it
- **Code:** Python 3, the official `braintree` SDK (sandbox), and an SQLite-backed store holding orders, RMAs, refund reservations and charge states.
- **Rail:** a fake rail that reproduces the card limits we observed in the sandbox.
- **Baselines:** two baselines that share no Counterfoil logic, no gate and a $200 cap.
- **Scenarios:** 22 scenarios (14 attacks in seven families, 8 genuine requests), split into dev and holdout.
- **Scoring:** outcome-based. It looks at what actually moved, where, and how much, and keeps attempt, intervention, harm and legitimate completion separate.
- **Models:** an OpenAI-compatible client runs local Ollama models and cloud models. The Claude runs went through the Astro AI Gateway.
- **Dashboard:** an AG Studio report over the runs.
- **Tests:** 174 tests cover the gateway rules, approvals, races and reconciliation, without an LLM.

## Challenges we ran into
- **Braintree changed the design.** Our first attack ("refund $120 on a $40 order") is something Braintree already refuses on cards (91521), so it couldn't be our selling point. We rebuilt the gate around the return authorisation, which only the merchant has.
- **Mocked PayPal is too permissive.** In the sandbox it accepted refunds above the transaction total. We decided never to count that as a Counterfoil catch, and our fake rail enforces the card limits instead.
- **Honest scoring.** An injection the model ignores is not a gate success, and a blocked read is not a leak. Separating "agent misled" from "harm" forced us to say "stopped 4 of 4 attempts", not "7/7".
- **Our own runs found two bugs.** The agent used the Reader's field name for quantity and the gate rejected a genuine reorder, and a scenario setup counted a refund twice. Both were fixed, with tests.

## Accomplishments that we're proud of
- **Zero harmful outcomes** with Counterfoil in 126 attack runs across six models (three repeats each), without blocking a single genuine request. The one refund held for review is a $300 return that store policy says needs a person. (A later qwen3 run got an inflated reorder through the earlier gate; see the note under the table.)
- **Attacks that pass both baselines.** Over-refunds, split refunds and replays all stay below the transaction total, so neither Braintree nor a $200 cap stops them.
- **Approvals that can't be replayed or stretched.** Each one is bound to the exact arguments and to the refund state the human saw.

## What we learned
- **Payment rails protect the transaction, not the business rule.** The gap between them is the merchant's to close, and it is closed with the merchant's own records, not with smarter prompts.
- **Better models are fooled less often, but not never.** Sonnet 5 was misled in 5 of 21 attack runs and Opus 5.5 in 6, against 12 for qwen2.5.
- **Measure attempts and harm separately.** Otherwise a model that ignores an injection looks like a gate success.

## What's next
- **More evidence:** more repeats on different days, the untouched holdout set, more models (including Vultr Serverless Inference), and end-to-end runs against the Braintree sandbox (`--rail braintree`).
- **Review flow:** a review queue in the dashboard where staff approve or reject held calls.
- **PayPal REST, measured:** the PayPal REST rail (`--rail paypal`, ADR 0008) puts the same gate in front of Agent Toolkit's `create_refund`; it is tested with a faked HTTP layer and still needs a run against a real PayPal REST sandbox.
- **Privacy in a real store (KVKK / GDPR):** the demo uses fictional customers and test money. A real store would tell customers that an AI agent reads their e-mail, that calls are checked automatically and that staff review the held ones (an information notice). Human review of held calls also answers the right to object to purely automated decisions (KVKK art. 11/1-g, GDPR art. 22). The review screen shows only the order, the items and the amount; card data stays with Braintree as a vault token. If e-mails go to a model hosted abroad, that is a cross-border transfer that needs its legal basis (KVKK art. 9); a local model avoids it.

## Built with
python, braintree (Python SDK, sandbox), mocked PayPal (Braintree sandbox), sqlite, openai-python (OpenAI-compatible client), ollama, qwen2.5, claude (Haiku 4.5, Opus 5.5 via Astro AI Gateway), astropods, pytest, next.js, react, typescript, ag-grid / ag-studio, three.js, blender
