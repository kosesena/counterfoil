# Counterfoil dashboard (AG Studio)

One AG Studio report over the evaluation runs: what the AI transaction agent tried to do with the money, what each gate decided, and what actually reached Braintree.

- **Overview** shows the condition and model filters and four numbers: attack runs, agent misled, wrong money reached the rail, and genuine requests handled right. Below them are a chart of harm against agent misled per condition, a donut of gate decisions, and a pivot of harm by model × attack family.
- **Held for review** shows the calls the gate did not let straight through: APPROVAL (waits for the merchant) and BLOCK (never reaches Braintree). It opens on the Counterfoil condition and has a model filter. Two tiles give counts with their denominators, never a summed amount. The first is attack e-mails: how many of the attack money calls were blocked or held. The second is genuine e-mails: how many were completed, and how many were sent to review as store policy requires. Below them is a grid of pending approvals and blocked calls, one row per call and no total row, with the store record, the Reader's hand-off and the agent's request side by side. Then a ranking of the checks that fired and the decision mix on money calls. Money appears only per call, never added up across models and repeats.
- **Why held, why blocked** is a custom widget on that page. For each held or blocked call, the **case agent** (`app/case-agent.ts`) builds a case file: the three amounts side by side, the refunds and reservations already on the order, the checks that fired, and one sentence on why. The agent runs on AG Studio's agent framework (`createAiHarness` + `clientToolRunner`). Studio runs the loop and the tools, and fixed rules choose each round's tool calls (no LLM, no key). The agent has three read tools, each a fixed query through Studio's own `execute_query` tool, and one display tool. None of them can approve, reject or move money, and the dashboard data holds no e-mail text, so nothing a customer writes can steer it. Approving stays with the merchant in the live demo, where the gate re-checks the call.
- **Agent calls** lists every refund and charge the agent attempted. Each row shows the store's approved amount, the decision, the reason codes and the rail result.
- **Braintree, checked from both sides** (Overview, under the evidence board; `app/rail-checks.tsx`) shows a sandbox record of the rail-side checks: the store-wide refund sweep (a refund through the gate, one made straight on Braintree, and the sweep reporting the second with its Braintree id) and what Braintree refuses on its own on a test card, mocked PayPal and the dispute test card. `scripts/record_rail_checks.py` records it (needs the Braintree sandbox keys); the export adds the newest `results/*-braintree-rail-checks.json` as `railChecks`.

## Run

```bash
# 1. export the saved runs (from the repo root)
.venv/bin/python scripts/export_dashboard.py     # writes dashboard/public/counterfoil-data.json

# 2. start the dashboard
cd dashboard
npm install
npm run dev                                      # http://localhost:3000
npm run build                                    # static site in out/, host anywhere
```

Live: **https://counterfoil-dashboard.vercel.app** (deployed as a static site: `npm run build`, then `vercel deploy --prod` from the `out/` copy).

No credentials are needed. The data is a static JSON file.

The AG Studio licence key is optional: set `NEXT_PUBLIC_AG_STUDIO_LICENSE`. Without it Studio shows a watermark and logs a licence notice. The AG Grid team said on the hackathon Discord that this is not penalised in judging. AG Studio is commercially licensed. The agent framework belongs to the "Pro with AI" tier, which the 45-day trial key covers. The case agent uses only the exported framework API (`createAiHarness`, `clientToolRunner`, `getAiTools`). It does not register Studio's assistant panel module, so the page stays in view mode.

## Data

`scripts/export_dashboard.py` flattens `results/*.jsonl` into seven related tables:

| Table | One row per |
|---|---|
| `runs` | scenario × condition × repeat × model |
| `calls` | tool call the agent made, with what the store record allows and what the Reader handed off |
| `findings` | gate check that fired on a call |
| `ledger` | refund or reservation already on the order when a call was held or blocked |
| `scenarios` | scenario |
| `orders` | order |
| `returns` | return authorisation (RMA) |

The relations are `calls → runs → scenarios`, `calls → orders`, `calls → returns`, `findings → calls` and `ledger → calls`. Harm rate, agent-misled rate and clean-handled-right rate are AG Studio expressions over the 0/1 flags.

The page code here is our own. PayPal's `hackathon-paypal-ag-grid-boilerplate` was read only as a reference for the AG Studio API.
