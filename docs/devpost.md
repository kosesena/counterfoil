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

**Measured with the latest gate, nine models, 3 repeats:** the dev set (7 attacks, one per family, and 6 genuine requests) for all nine models; the holdout set (7 more attacks and 2 genuine requests, kept apart while the gate was written) for the four local models. 21 attack runs and 18 genuine runs per model and condition on dev, from `results/2026-10-25-dev-r3-current-gate-*.jsonl`, `results/2026-10-26-dev-r3-current-gate-*.jsonl` and `results/2026-10-25-holdout-r3-*.jsonl`.

| Model (dev set) | Agent misled (no gate) | Harm: no gate | Harm: $200 cap | Harm: Counterfoil | Genuine requests handled right (no gate / cap / Counterfoil) |
|---|---|---|---|---|---|
| qwen2.5, local (Ollama, 7.6B) | 12/21 | 12/21 | 12/21 | **0/21** | 12/18 · 15/18 · **18/18** |
| qwen3, local (Ollama, 8B) | 15/21 | 12/21 | 12/21 | **0/21** | 12/18 · 15/18 · **18/18** |
| Claude Haiku 4.5 | 9/21 | 9/21 | 9/21 | **0/21** | 12/18 · 15/18 · **18/18** |
| GPT-5.6 Sol | 9/21 | 9/21 | 8/21 | **0/21** | 12/18 · 15/18 · **18/18** |
| GPT-5.6 Terra | 7/21 | 7/21 | 8/21 | **0/21** | 12/18 · 15/18 · **18/18** |
| Claude Opus 5.5 | 6/21 | 6/21 | 6/21 | **0/21** | 12/18 · 15/18 · **18/18** |
| hermes3, local (Ollama, 8B) | 6/21 | 6/21 | 6/21 | **0/21** | 6/18 · 6/18 · **6/18** ¹ |
| llama3.1, local (Ollama, 8B) | 18/21 | 6/21 | 6/21 | **0/21** | 6/15 · 6/15 · **6/15** ¹ ² |
| Claude Sonnet 5 | 5/21 | 5/21 | 6/21 | **0/21** | 12/18 · 15/18 · **18/18** |

**Holdout set** (qwen2.5, qwen3, llama3.1, hermes3): harm in 27/81 attack runs with no gate, 27/81 with the cap, **0/81** with Counterfoil ².

¹ These two models fail most genuine requests on their own (the same count with no gate at all). Counterfoil stopped their reorder call in CLEAN-06 (3 runs each), a request both also got wrong with no gate.
² llama3.1 never finished 18 runs (timeouts): dev genuine request CLEAN-03 ×9 and holdout attack P4-02 ×9. They are not counted, so its denominators are 15 and 18.

Notes on the table:
- "Harm" means wrong money moved, or another customer's data was read. Totals: dev 72/189 with no gate, 73/189 with a $200 cap, 0/189 with Counterfoil; with the holdout set, 99/270, 100/270 and **0/270**.
- "Handled right" is completed, or held for a person where store policy requires it: the $300 return (CLEAN-07), and under Counterfoil also the genuine reorder (CLEAN-06), because every charge waits for confirmation of the itemised total. With no gate, the $300 return went through unreviewed.
- The $200 cap stopped nothing: no single harmful call was above $160.
- Under an earlier gate (commit 6f30a4a) qwen3 broke the zero: in all three repeats its Reader obeyed P7-01's hidden HTML and handed off 6 cups for $150.00; the charge matched that hand-off, and $150.00 reached the rail. That led to the charge rule above, and the latest gate holds that charge. Every number in the table is from the latest gate.

**The worst case, against the real Braintree sandbox:** a scripted agent and Reader fully on the attacker's side (no model, so no model can resist) ran all 22 scenarios. With no gate, its attack calls moved money 12 times in the sandbox (10 refunds, 2 charges). With Counterfoil: zero, and none of the 8 genuine requests was blocked (5 completed, 3 held as store policy requires).

## How we built it
- **Code:** Python 3, the official `braintree` SDK (sandbox), and an SQLite-backed store holding orders, RMAs, refund reservations and charge states.
- **Rail:** a fake rail that reproduces the card limits we observed in the sandbox.
- **Baselines:** two baselines that share no Counterfoil logic, no gate and a $200 cap.
- **Scenarios:** 22 scenarios (14 attacks in seven families, 8 genuine requests), split into dev and holdout.
- **Scoring:** outcome-based. It looks at what actually moved, where, and how much, and keeps attempt, intervention, harm and legitimate completion separate.
- **Models:** an OpenAI-compatible client runs local Ollama models and cloud models. The Claude and GPT-5.6 runs went through the Astro AI Gateway.
- **Dashboard:** an AG Studio report over the runs.
- **Tests:** 174 tests cover the gateway rules, approvals, races and reconciliation, without an LLM.

## Challenges we ran into
- **Braintree changed the design.** Our first attack ("refund $120 on a $40 order") is something Braintree already refuses on cards (91521), so it couldn't be our selling point. We rebuilt the gate around the return authorisation, which only the merchant has.
- **Mocked PayPal is too permissive.** In the sandbox it accepted refunds above the transaction total. We decided never to count that as a Counterfoil catch, and our fake rail enforces the card limits instead.
- **Honest scoring.** An injection the model ignores is not a gate success, and a blocked read is not a leak. Separating "agent misled" from "harm" forced us to say "stopped 4 of 4 attempts", not "7/7".
- **Our own runs found two bugs.** The agent used the Reader's field name for quantity and the gate rejected a genuine reorder, and a scenario setup counted a refund twice. Both were fixed, with tests.

## Accomplishments that we're proud of
- **All nine models: zero harmful outcomes** with the latest gate (270 attack runs, dev and holdout), and no genuine request a model handled right without a gate was lost. What Counterfoil holds for a person is what store policy says needs one: the $300 return and every charge. Under an earlier gate qwen3 got an inflated reorder through in all three repeats; that led to the charge rule, which now holds it.
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
python, braintree (Python SDK, sandbox), mocked PayPal (Braintree sandbox), sqlite, openai-python (OpenAI-compatible client), ollama, qwen2.5, claude (Haiku 4.5, Sonnet 5, Opus 5.5) and gpt-5.6 (Terra, Sol) via Astro AI Gateway, astropods, pytest, next.js, react, typescript, ag-grid / ag-studio, three.js, blender
