# Counterfoil live demo

A single web page where you pick a scenario (or write your own refund/charge email) and watch one run under the
three conditions side by side: no gate, a $200 cap, and Counterfoil. For each one you see what the Reader extracted
from the email, every tool call the payments agent made, the gate's decision on it (PASS / APPROVAL / BLOCK with
reason codes), and whether money reached the rail.

Every run goes through `scripts/run_eval.run_one`, the function that produced the evaluation numbers. The server
only adds what a public URL needs.

| Mode | What it does | Needs |
|---|---|---|
| `replay` (default) | Returns a saved run from `results/*.jsonl` exactly as measured. No model call, no cost. | nothing |
| `live` | Runs the Reader and the payments agent on a model configured on the server. | a model + key in the server env |

Saved sources include dev and holdout runs, plus the November follow-up cohorts. Replay availability is listed
per scenario by `/api/scenarios`; a new email needs live mode.

## HOMI story player

The top of the page tells scenario P6-01 (split refund) in five steps at HOMI's return station: through the gates,
four cups scanned, the agent asks for 60 USD and the screen turns amber, the manager's tablet (60 + 60 = 120 > 100,
rejected, 40 left), the 40 USD receipt. Back/Next only; nothing advances on its own. The data beside the scene is the
recorded P6-01 run under Counterfoil (the saved run picked in the source menu); after a visitor pays with PayPal and
runs the Counterfoil refund in section 3, it switches to their Braintree sale, the BLOCK finding and the refund id.

Files: `demo/static/story.js` (three.js 0.170.0 and its Draco decoder come pinned from jsDelivr) and
`demo/static/story/step-1..5.jpg`, what phones (< 760 px) see instead of WebGL (Codex's step previews). The scene is
served straight from where Blender exports it (`tools/export_story_glb.py`), as `/story/homi-story.glb` and
`/story/homi-story.json`: one `HOMI_STORY` animation, cameras `HOMI_OVERVIEW` and `HOMI_STEP_1..5`, a frame range per
step and the scan events. The recorded run shows the scene's own screen lettering; the visitor's run draws
`HOMI_SCREEN_MAT` as a canvas from their data. The tablet's screen has no UVs, so their figures sit next to it as
HTML. The GLB is about 25 MB and only loads on wider screens, once the section is near the viewport.

## Run locally

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn demo.app:app --reload          # http://localhost:8000
```

That gives you replay mode. For live mode, set **one** of these in `.env` (it is git-ignored) or in your shell:

```bash
DEMO_MODEL=haiku-5.5            # any preset in counterfoil/llm.py; its key comes from the preset's env var
ANTHROPIC_API_KEY=...

# or any OpenAI-compatible endpoint (local Ollama, Vultr Serverless Inference, ...)
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5-8k
LLM_API_KEY=ollama
```

Unlike `run_eval.py`, the demo does not fall back to a local Ollama. If neither option is set, live mode stays off
and the page says why.

**Rail.** The demo uses the in-memory `FakeRail` unless all of `BRAINTREE_ENVIRONMENT=sandbox`,
`BRAINTREE_MERCHANT_ID`, `BRAINTREE_PUBLIC_KEY` and `BRAINTREE_PRIVATE_KEY` are set. With them, live runs create
and refund real **sandbox** transactions (`SandboxRail`). Production Braintree keys are refused by `BraintreeRail`.

Tests: `.venv/bin/pytest -q` (the demo's are in `tests/test_demo.py` and use a scripted fake LLM, so they need no
key and no network).

## API

| | |
|---|---|
| `GET /api/scenarios` | All scenarios: the email, the attacker's goal, the expected decision, and which saved runs include it |
| `GET /api/config` | Whether live mode is on (and which model), the rail, the limits, the replay sources, the fixture store |
| `POST /api/run` | `{scenario_id \| email, condition, mode, source?}` → one row in run_eval's shape, plus `demo` metadata |
| `POST /api/checkout/rail-rules` | Braintree keys only. Fresh sandbox sales sent straight to Braintree (no agent, no gate): a test card (refund before settlement → `91506`, `testing.settle_transaction`, above the sale → `91521`, after a full refund → `91512`), the same calls on mocked PayPal (all accepted), and a sale on the dispute test card `4023898493988028` with the gate's check (`TRANSACTION_DISPUTED`) next to Braintree's own refund (accepted). About 15 sandbox calls per request, under the checkout rate limit |

| `POST /api/braintree/webhook` | Braintree keys only. Braintree's form post (`bt_signature`, `bt_payload`), verified with `webhook_notification.parse`; unverified → 403, nothing recorded. A dispute notification on a purchase locks its refund runs (`TRANSACTION_DISPUTED`). Answers `{kind, action, duplicate}` |
| `GET /api/braintree/events` | The audit of verified notifications, newest first: kind, subject (transaction or refund id), when Braintree sent it, what the store did (`dispute_locked`, `dispute_unlocked`, `refund_failed`, `flagged`, `checked`, `ignored`, ...) and the details |

`condition` is `none`, `cap` or `counterfoil`. `email` is `{from, subject, body_text, body_html?, attachment_text?}`.
`source` (replay only) is a `results/*.jsonl` file stem; the default is the qwen2.5 run, or `DEMO_REPLAY_SOURCE`.

## Abuse limits (live mode)

| | Default | Env |
|---|---|---|
| Live runs per client IP | 6 per 10 min | `DEMO_RATE_LIMIT`, `DEMO_RATE_WINDOW_S` |
| Model calls per UTC day, all clients | 300 | `DEMO_DAILY_LLM_CALLS` |
| Live runs in flight | 2 (then 503) | `DEMO_MAX_CONCURRENT` |
| Email size (subject + body + HTML + attachment) | 4000 chars | `DEMO_MAX_EMAIL_CHARS` |
| Agent budget | 6 turns, 8 tool calls (same as the evaluation) | `DEMO_MAX_TURNS`, `DEMO_MAX_CALLS` |
| Model timeout | 60 s | `DEMO_LLM_TIMEOUT_S` |
| Request body | 64 KB | |

- **Shared Reader.** The three conditions of one email share one Reader output (an LRU cache keyed by scenario or
  email hash). So "Run under all three" costs one Reader call, and the conditions differ only in the gate, as in
  the evaluation.
- **Fixture store only.** A pasted email gets the baseline fixture store and the scenarios' business date. Its
  sender is resolved from the From address like any other email, and an unknown sender gets no customer. Whatever
  gate is chosen, the rail is wrapped in `demo/scope.py`: refunds and voids reach it only for the store's own
  transaction ids, and charges only for the store's vaulted tokens. Anything else fails as "not found" before the
  rail, so even "no gate" cannot touch a transaction outside the story.
- **Secrets.** Keys stay in the server process. `/api/config` reports the model id and the rail kind, never a key. Live rows are scrubbed of any configured key/secret value before they leave, in case a
  provider error message quotes one.
- **IP limit is best effort.** Behind a proxy, uvicorn runs with `--proxy-headers` so visitors are told apart, but
  `X-Forwarded-For` can be spoofed. The daily model-call cap is the hard bound on cost.

## Deploy on Render (Starter plan)

1. Push the branch. In Render: **New → Blueprint**, pick this repo; `render.yaml` defines the web service
   (Docker, paid Starter plan, health check `/healthz`). While the repo is private, Render needs access to it through
   its GitHub app.
2. Leave every secret empty for a replay-only demo, or fill `DEMO_MODEL` and its key (e.g. `haiku-5.5` +
   `ANTHROPIC_API_KEY`) in the dashboard. Optionally add the three `BRAINTREE_*` values for the sandbox rail.
3. Deploy, then open the `.onrender.com` URL and verify `/healthz`. The Blueprint selects Starter rather than
   the sleeping free instance; `render.yaml` is the source of truth for the configured plan.

## Braintree webhooks (sandbox Control Panel)

Needs the demo deployed with the three `BRAINTREE_*` values (above), at a public HTTPS URL.

1. Sign in to the Braintree **sandbox** Control Panel (sandbox.braintreegateway.com). Gear icon → **API** →
   **Webhooks** → **Create new webhook**.
2. Destination URL: `https://<your-service>.onrender.com/api/braintree/webhook` (set up for
   `counterfoil-demo.onrender.com` on 29 Oct).
3. Tick the eight Dispute notifications (Accepted, Auto Accepted, Disputed, Expired, Lost, Opened, Under Review, Won)
   and Refund → Refund Failed. On 29 Oct the sandbox offered no settlement or disbursement kinds. Counterfoil records
   and ignores any other kind. Create the webhook.
4. Press **Check URL** next to it. Braintree posts a `check` notification; `GET /api/braintree/events` on the demo
   should list it with action `checked`. If the instance was asleep, press it again after the first request wakes it.
5. Real chargeback: run section 4 of the demo ("What Braintree refuses on its own"). Its dispute-card sale gets a
   chargeback within seconds; the `dispute_opened` delivery should appear in `/api/braintree/events` with Braintree's
   own dispute id. Observed on 29 Oct: delivered about two seconds after Braintree sent it, action `dispute_locked`.

Without `DEMO_EVENTS_DB`, events are kept in memory and disappear on restart, regardless of instance plan.
Set `DEMO_EVENTS_DB=/path/file.sqlite` on a mounted persistent disk to retain them. The current Blueprint does
not configure that disk. Braintree retries deliveries that do not get a 2xx; a repeated delivery is recorded once.

## Deploy on a Vultr VM

On a small Ubuntu instance with Docker installed:

```bash
git clone https://github.com/kosesena/counterfoil && cd counterfoil
docker build -t counterfoil-demo .
cat > demo.env <<'EOF'        # chmod 600; never commit
LLM_BASE_URL=https://api.vultrinference.com/v1
LLM_MODEL=<a tool-calling model from your Vultr Serverless Inference list>
LLM_API_KEY=<vultr inference key>
DEMO_DAILY_LLM_CALLS=300
EOF
chmod 600 demo.env
docker run -d --restart unless-stopped --name counterfoil-demo --env-file demo.env \
  -p 127.0.0.1:8000:8000 counterfoil-demo
```

Put TLS in front of it, for example with Caddy (`/etc/caddy/Caddyfile`):

```
demo.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Open ports 80 and 443 in the Vultr firewall group, and keep 8000 closed (the container is bound to localhost
above). To update, run `git pull && docker build -t counterfoil-demo . && docker rm -f counterfoil-demo`, then the
same `docker run` command again.

### Approval and restart validation

The [3 November approval/recovery protocol](../docs/arastirma/2026-11-03-approval-recovery.md) checks approvals,
expiry, replay and locally injected payment failures against Braintree sandbox. The API tests also verify that
recreating the app rejects old purchase/approval IDs. Checkout purchases, holds and per-run ledgers remain in
memory: `DEMO_EVENTS_DB` retains webhook events/disputes only. Restart fails closed rather than resuming checkout;
unknown payment outcomes require reconciliation before any new attempt.
