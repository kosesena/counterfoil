# Counterfoil — English judge walkthrough

1. Download `counterfoil-demo-review.mp4` from the [reviewed delivery](https://github.com/kosesena/counterfoil/releases/tag/demo-review-2026-11-03) and watch it. Its 76-second central segment is an uninterrupted browser capture at original speed. It shows executed sandbox payments with recorded agent calls.
2. Open https://counterfoil-demo.onrender.com. Select “Watch a recorded run”, P6-01, then “Compare the three checks”. Inspect the split-refund attempt and each gate decision.
3. To test actual sandbox execution, use “Complete the test with PayPal”. Create the USD 200 sandbox purchase, choose the Counterfoil refund path, inspect the blocked USD 60 attempt and the held USD 40 correction, then approve the correction. Inspect the resulting Braintree sandbox refund. This uses a mocked PayPal account, not a wallet login.
4. Open https://counterfoil-dashboard.vercel.app and inspect the October and November cohorts separately. “Held for review” on this dashboard is an illustrated story, not the operational checkout approval panel.
5. Fresh model calls are available in the separate “Try live AI” mode. They are not needed to replay the recorded comparison.

The hosted service currently permits 6 relevant requests per client per 10 minutes and has a daily model budget. Avoid repeated runs; preserve unknown payment outcomes rather than automatically retrying. Local setup is documented in demo/README.md. API credentials must be configured privately, never committed to the public repository.

## Evidence
- Continuous source: live-demo/continuous-browser-demo.mp4 in the reviewed ZIP
- Capture outcome: sandbox-capture-evidence.json in this review package.
- October results: dashboard/public/counterfoil-data.json in the source repository.
- Recovery protocol: docs/arastirma/2026-11-03-approval-recovery.md.

This document is prepared for review. Public source, public YouTube link and a verified free judge-access route are release checks, not completed claims.

The live hosted payment route was captured successfully on 3 November. Recheck availability before submission and keep a working hosted route or complete local build instructions available throughout judging. [Official access requirements](https://paypalaihackathon.devpost.com/rules).
