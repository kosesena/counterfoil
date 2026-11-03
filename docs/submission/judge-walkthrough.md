# Judge walkthrough — Counterfoil

## Two-minute path, no accounts or model call needed
1. Open https://counterfoil-demo.onrender.com and keep **Watch a recorded run** selected.
2. Choose **Nella asks for more** (P6-01). Press **Compare the three checks**.
3. Compare the recorded payment calls: the split-refund request reaches the simulated rail with no gate and the USD 200 cap; Counterfoil blocks it against the remaining return entitlement.
4. Use the store walkthrough to inspect the Reader, Runner and gate decision. The comparison is replayed evidence, not newly generated AI output.
5. Open https://counterfoil-dashboard.vercel.app. Inspect October results, then the newer-test selector. Keep each cohort's denominator and limitations with its result.
6. Open **Held for review**. This dashboard section is an illustrated story and recorded evidence, not an operational approval queue.

## Optional interactive sandbox
The demo's **Complete the test with PayPal** section creates Braintree sandbox transactions. Its PayPal button uses a mocked PayPal account; it is not a real wallet login. Use the Counterfoil refund path and review the held correction before approving. Only test money is involved.

The **Try live AI** mode makes new model calls and is rate limited; it is not necessary to verify the recorded evidence. If its daily quota is exhausted, the recorded path remains available.

## Evidence map
- October aggregate: `dashboard/public/counterfoil-data.json`
- November cohorts: `dashboard/public/recent-evidence.json` and `dashboard/public/evidence/`
- Approval/recovery: `results/2026-11-03-approval-recovery.json`
- Recovery protocol and limitations: `docs/arastirma/2026-11-03-approval-recovery.md`
- Current test totals: `docs/quality.md`

## Submission gates still requiring completion
- Upload the delivered video to the chosen video host and confirm a reviewer can open its URL without signing in.
- Provide reviewer access to the currently private GitHub repository, or intentionally make it public.
- Check the actual event form's current duration, asset and eligibility requirements before submission; this package does not claim those rules were verified.
- Paste the text and links into the submission form and submit. No submission or repository-visibility change has been made by preparing this package.
