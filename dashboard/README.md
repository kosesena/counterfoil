# Counterfoil dashboard (AG Studio)

One AG Studio report over the evaluation runs: what the AI transaction agent tried to do with the money, what each gate decided, and what actually reached Braintree.

- **Overview** shows the condition and model filters and four numbers: attack runs, agent misled, wrong money reached the rail, and genuine requests handled right. Below them are a chart of harm against agent misled per condition, a donut of gate decisions, and a pivot of harm by model × attack family.
- **Agent calls** lists every refund and charge the agent attempted. Each row shows the store's approved amount, the decision, the reason codes and the rail result.

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

No credentials are needed. The data is a static JSON file.

The AG Studio licence key is optional: set `NEXT_PUBLIC_AG_STUDIO_LICENSE`. Without it Studio shows a watermark and logs a licence notice. The AG Grid team said on the hackathon Discord that this is not penalised in judging.

## Data

`scripts/export_dashboard.py` flattens `results/*.jsonl` into five related tables:

| Table | One row per |
|---|---|
| `runs` | scenario × condition × repeat × model |
| `calls` | tool call the agent made |
| `scenarios` | scenario |
| `orders` | order |
| `returns` | return authorisation (RMA) |

The relations are `calls → runs → scenarios`, `calls → orders` and `calls → returns`. Harm rate, agent-misled rate and clean-handled-right rate are AG Studio expressions over the 0/1 flags.

The page code here is our own. PayPal's `hackathon-paypal-ag-grid-boilerplate` was read only as a reference for the AG Studio API.
