# Architecture decisions

Short records of the decisions that shape Counterfoil: the context, what was considered, what was chosen and what
followed. Format after Michael Nygard's ADRs. Status of this set: **draft, written with Claude Code from the project
notes; Sena reviews and rewrites each one in her own words.**

| # | Decision | Date |
|---|---|---|
| [0001](0001-trust-the-store-record-not-the-email.md) | Trust the store's record, not the e-mail | 2026-10-23 |
| [0002](0002-two-agents-reader-and-transaction.md) | Two agents: a tool-less Reader and a Transaction agent that never sees the e-mail | 2026-10-22 |
| [0003](0003-per-transaction-checks-not-a-spending-cap.md) | Per-transaction record checks instead of a spending cap | 2026-10-23 |
| [0004](0004-the-gate-holds-the-only-rail-credentials.md) | The gate holds the only payment-rail credentials | 2026-10-22 |
| [0005](0005-approvals-are-single-use-and-bound.md) | Human approvals are single-use, time-limited and bound to the exact call | 2026-10-23 |
| [0006](0006-check-what-the-call-does-not-what-the-text-says.md) | Check what the call would do, not what the text looks like | 2026-10-23 |
| [0007](0007-braintree-sandbox-with-mocked-paypal.md) | Braintree sandbox with mocked PayPal instead of the PayPal REST API | 2026-10-23 |
| [0008](0008-paypal-rest-rail-in-front-of-agent-toolkit.md) | A PayPal REST rail, so the gate sits in front of Agent Toolkit's `create_refund` | 2026-10-24 |
| [0009](0009-mcp-server-with-toolkit-shaped-tools.md) | An MCP server whose tools look like Agent Toolkit's, with the gate in front of the rail | 2026-10-29 |
