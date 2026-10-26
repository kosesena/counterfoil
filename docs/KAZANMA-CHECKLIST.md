# PayPal AI Hackathon — winning checklist (26 Oct 2026)

Source: paypalaihackathon.devpost.com home page + official rules (re-read on 26 Oct), repo `origin/main` 52c6dd3, live addresses on the evening of 26 Oct. Status: ✅ done · ⚠️ partial / risk · ❌ missing.

**Deadline: 12 Nov 12:00 PT = 23:00 Türkiye time.** Judging 1–15 Dec, results ~21 Dec. Meta (until 5 Nov) and Vultr (3–8 Nov) overlap → the real window is 8–12 Nov.

Nobody can guarantee first place: judging is subjective, the criteria are equally weighted and we do not see the competitors. This list is to make sure we collect every point within our reach.

## A. Eligibility (Stage 1, pass/fail) and required submission

| # | Requirement (rule text) | Status | To do |
|---|---|---|---|
| A1 | Use PayPal technology meaningfully (Braintree counts as a PayPal service in the rules) | ✅ real Braintree sandbox: sale, refund, void, vault, lookup | — |
| A2 | Use AI meaningfully | ✅ two agents (Reader + Runner), measured with 9 models; 180 tests (`tests/`), CI `tests` green on main | — |
| A3 | Working prototype; mockup/static demo **not accepted** | ⚠️ dashboard and demo are live, but the demo is only in **replay** mode (live model off) | Turn on live mode (model + key in Render env) or state clearly that replay is "identical to the measured run" |
| A4 | Documentation the judges will understand | ✅ README, 90-second box, ADRs | — |
| A5 | **Public** repo + open source license visible in About | ❌ repo is **PRIVATE**; MIT file exists, GitHub detects it | Make public before 12 Nov (repeat the secrets/advisor-name scan) |
| A6 | Setup instructions + if needed test account / API key / sandbox login | ⚠️ quick start exists; `--rail braintree` needs a key | Add to README a "keyless path (fake rail, worst-case, replay)" + a "open your own free Braintree sandbox account" step; secret keys are not shared |
| A7 | Text description | ⚠️ `docs/devpost.md` draft exists; project not yet created on Devpost | Align the draft with the latest numbers (0/270, 99/270, 100/270, 150/183), fill in the form |
| A8 | List the AI tools used and how they were used | ✅ README "Tools used" | Same in the Devpost form |
| A9 | **Video under 3 min, public on YouTube** | ❌ missing; storyboard is old (40/120) | Biggest gap, see C below |
| A10 | No unauthorised third-party brands / music in the video | ⚠️ model logos are already not used | Royalty-free music; no IKEA etc. on screen; PayPal/Braintree logos from official assets |
| A11 | All submission material in English | ✅ (26 Oct) every doc translated; left in Turkish on purpose: the Reader's hand-off keys (they are in every measured run's prompt; glossary in the README), the .blend collection names, raw tool output, proper names | — |
| A12 | New project or "significantly updated" during the period | ✅ first commit 23 Oct (period started 1 Oct); thesis link in the description | One sentence in the description: "the repo was opened from scratch on 23 Oct" |
| A13 | Project accessible free and without restriction **until the end of judging (15 Dec)** | ⚠️ `render.yaml` now puts the demo on a paid `starter` instance (no sleep) and the dashboard on a Render static site (no sleep); the Türk Telekom filter blocks *.vercel.app / *.onrender.com on some lines | Sena: apply the Blueprint and the paid plan on Render; then switch the README links from Vercel; PR #25 (own domain) awaiting decision |
| A14 | Prize rule: at most 1 Grand + 1 Sponsor **or** 1 Honourable Mention + 1 Sponsor | ✅ target: Grand + AG Grid | — |

## B. Judging criteria (all five equally weighted)

| Criterion | What the judges ask | Where we are | To close the gap |
|---|---|---|---|
| **Technological Implementation** | How deep and skilful is the PayPal + AI use; working, non-trivial work | Strong: gate + tests, 9 models, real Braintree, worst-case 0/14. Weak side: only basic transaction APIs from Braintree; Agent Toolkit path via fake HTTP | A "second check" feature from Braintree (to be chosen when the research is done: line item data / refund webhook / transaction search) |
| **Design** | A coherent product experience, not just technical proof | Good: felt dashboard, HOMI, 3D story. Missing: the "Held for review" page was not built to Codex's design; nobody has tried the live payment flow end to end in the demo | Held for review page; Sena should try the live QR payment once |
| **Potential Impact** | Real audience, a specific problem, does the shown solution solve that problem | Medium: small shop refund agent. The only sourced figure ($103 billion) is not agent-specific | Name the user in one sentence ("a small online shop that lets AI read refund emails"); give the figure with honest context |
| **Innovation/Idea** | Is it new, how does it differ from existing ideas | Strong: merchant side, per-transaction comparison against the record; competitor table in the README | One sentence in the video: "others look at how much was spent, we look at whether this money is owed" |
| **Presentation** | Does the video show the project working end to end; problem, audience, why it matters | ❌ no video | See C below. The "Best Demo Delivery" honourable mention is also tied to this criterion |

## C. Video plan (3 min, the judges' main material)

- 0:00–0:15 scene: hidden instruction in the customer note, the agent asks for $60 (P6-01)
- 0:15–1:30 working product: live demo, three conditions side by side, the call Counterfoil held, the manager's approval screen, real Braintree transaction id
- 1:30–2:15 proof: 0/270 vs 99/270, worst-case 0/14; "the agent is still fooled, no money goes out"
- 2:15–2:45 why PayPal + for whom + difference from competitors
- 2:45–3:00 limits in one sentence + repo
- Royalty-free music, real screen recording, separate English subtitles

## D. Against the GlovesOn lessons

| Lesson | Status |
|---|---|
| The main claim must not rest on a fake system | ✅ results are real Braintree sandbox transactions; the mock PayPal gap is written down by name |
| The sponsor product must be essential | ✅ "Why PayPal and Braintree" (PR #39) |
| 90-second box for the judges | ✅ (PR #39) |
| Measure the hard part, put the number first | ✅ |
| One-click demo, no microphone/key | ⚠️ replay exists; Render cold start and TT filter |
| Platform text + tags | ❌ no Devpost form yet; tags: Braintree, PayPal, AG Grid, Render, Astropods |

## E. Sponsor prize: AG Grid

- ✅ (26 Oct) The Overview has a section under the evidence board that names AG Studio and opens Held for review (case agent on Studio's agent framework) and Agent calls. Studio's own Overview page stays hidden: its run-level rates are computed over the joined calls table (wrong money about 26–28% against 24.9% over the runs). Still to do: show AG Studio in the README and the video.
- Render is also used (the demo is on Render), so it is eligible for the Render prize too; but only one sponsor prize can be won.

## F. Open risks

1. Sena has not yet tried the attack texts and the live QR payment herself.
2. **Fixed (26 Oct):** the live demo's default replay source was `2026-10-23-dev-qwen2.5-8k`, i.e. the **old gate** (`/api/config` → `replay_default`; `demo/replay.py` picked the first qwen2.5 file, `DEMO_REPLAY_SOURCE` was empty on Render). P6-01, shown by the 90-second box, gives the same result in both files (Counterfoil: no harm, 0 calls to the payment service; no gate and cap: $60.00 refund), but 12 of the 28 sources in the list are from the old gate (23–24 Oct). The default is now the newest current-gate qwen2.5 run and the 12 older sources are labelled "previous gate" in the menu (`demo/replay.py`, test in `tests/test_demo.py`).
3. Astropods credit ran out; a new cloud run depends on the card limit ($20).
4. Schedule: on 8–12 Nov, video + Devpost + making the repo public + AG Grid visibility all at once.

## F2. From the PayPal + Braintree research (for Technological Implementation)

Details and sources: [`arastirma/2026-10-26-paypal-braintree-features.md`](arastirma/2026-10-26-paypal-braintree-features.md) (English). All of them are in Braintree and can be done from Türkiye.

| # | To add | Why it earns points | Already there? |
|---|---|---|---|
| 1 | Payment-service-side line item check: `line_items` on the sale, `transaction_line_item.find_all` on the refund | Today all checks read the store record; this is a second check from outside the record. Deep use of PayPal | ✅ (26 Oct, `RAIL_ITEMS_MISMATCH`; worst-case decisions unchanged on all 66 rows, so the measured results stand) |
| 2 | `api_request_key` on refund and void (from order + RMA + amount) | If the agent retries, there is no double payment; must be tried once in the sandbox | ✅ (26 Oct; the sandbox enforces it: same key → same refund, other amount → `915232`; worst-case decisions unchanged on all 66 rows) |
| 3 | Block refunds on a transaction with an open dispute | Refund + chargeback = paying twice; shown in the demo with a test card | ✅ gate rule (26 Oct, `TRANSACTION_DISPUTED`; the sandbox itself let a full refund through on top of an open chargeback; worst-case decisions unchanged). Demo scene comes with #5 |
| 4 | Store-wide refund scan (`transaction.search`) | Lists refunds the store does not know about | ✅ (26 Oct, `counterfoil/reconcile.py` + `scripts/sweep_refunds.py`, run on the sandbox; on the dashboard Overview since 26 Oct) |
| 5 | Card + `testing.settle` in the demo, next to the mock PayPal | The "Braintree already rejects this" division of labour becomes visible live | ✅ (26 Oct, demo section 4 "What Braintree refuses on its own": card / mocked PayPal / dispute card, run on the sandbox) |

Note: PayPal's own agent products (Agent Ready, Store Sync) cover purchasing, not refunds. A strong sentence for the Innovation story.

## G. Priority order (points / hour)

1. Video (Presentation + Best Demo + indirectly every criterion)
2. Repo public + Devpost form + English summaries (eligibility risk)
3. Live demo access and the live mode decision
4. Make AG Grid visible (sponsor prize)
5. Braintree features in the order in F2 (1 and 3 first: most visible, least risk)
6. Move the demo replay default to the current gate (risk 2 in section F)
