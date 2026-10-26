# PayPal and Braintree developer features, and what Counterfoil should use (26 Oct 2026)

Two research passes over developer.paypal.com (PayPal REST, Braintree docs, Agent Ready), github.com/paypal/agent-toolkit and the braintree_python SDK. Claims marked **SDK-checked** were confirmed against the installed `braintree` 4.48.0 on 26 Oct. **UNVERIFIED** means no primary source was read for it. "TR" says whether it works from Türkiye: **BT** = in the Braintree sandbox, no PayPal account needed; **PP-acct** = needs a PayPal developer account, which can't be opened from Türkiye.

## What Counterfoil already uses

| Feature | Where |
|---|---|
| `transaction.sale` (mocked PayPal nonce, vaulted method), `refund`, `void`, `find` | `counterfoil/rail.py` (`BraintreeRail`) |
| `order_id` on every sale | `rail.py` |
| `line_items` on every sandbox sale, read back with `transaction_line_item.find_all`; the gate blocks a return record that exceeds them (`RAIL_ITEMS_MISMATCH`). Sandbox-checked 26 Oct on a mocked-PayPal sale: lines come back with quantity as a string (`'2'`), the refund transaction has none | `rail.py`, `gateway.py` (`_rail_items`), `spikes/braintree_line_items_spike.py` |
| Rail-side refund total per transaction: sum of `find(rid).amount` over `refund_ids`, skipping failed/rejected/declined/voided | `BraintreeRail.refunded_total` |
| `PayPal-Request-Id` on every PayPal REST money call; real `REFUND_AMOUNT_EXCEEDED` error shape | `counterfoil/paypal.py` |
| Gate in front of Agent Toolkit `create_refund` (Toolkit parameters) | `counterfoil/toolkit.py` |
| Refund window as a store rule | `gateway.py` (`OUTSIDE_REFUND_WINDOW`) |

## Braintree (BT, works from Türkiye)

| Feature | API | Relevance |
|---|---|---|
| **Line items on the sale** (up to 249: name, quantity, unit_amount, total_amount, product_code, kind) and read-back | `transaction.sale(... line_items=[...])`, `gateway.transaction_line_item.find_all(id)` — **SDK-checked** | **High.** A second, rail-side check of the refund against what was actually sold. The **refund** call itself takes no line items (`refund_signature` = amount, api_request_key, order_id, merchant_account_id, surcharge_amount — **SDK-checked**), so the comparison is against the original sale. |
| **Idempotency key** on sale, refund, void, credit, submit_for_settlement, reverse | `api_request_key` — **SDK-checked** on sale and refund | **High.** Derive it from (order, RMA, amount) so a retried agent call cannot pay twice. Docs describe the 30-day window for GraphQL only; whether the sandbox enforces the key sent through the SDK is **UNVERIFIED** — one sandbox test settles it. |
| **reverse** (void if unsettled, else full refund) | `transaction.reverse` — **SDK-checked** (new in 4.48.0) | **Medium.** A money-moving shortcut; if exposed to an agent it must be gated like refund. |
| **credit** (refund with no original sale) | `transaction.credit` | **High as a risk.** Never give it to the agent, or gate it hard. |
| **Transaction search** for refunds | `transaction.search(type == Credit, refund == True, order_id …)` | **High.** A store-wide sweep for refunds the store's records don't contain (today the check is per transaction). |
| **Disputes** | `dispute.search/find/accept/...`; test card `4023898493988028` gives an already-disputed sale | **High.** New rule: block a refund on a transaction with an open dispute (refund + chargeback = paying twice). |
| **Sandbox settlement** | `gateway.testing.settle_transaction` and friends | **High for the demo.** Shows the rail's own refusals live on a card (91506 → settle → 91521 / 91512) next to mocked PayPal, which does not enforce the refund total (our test, ADR 0007). |
| Webhooks | Transaction webhooks fire only for ACH/SEPA; no refund webhook for card or PayPal; `refund_failed` exists in the SDK but not in the webhook docs (**UNVERIFIED**); dispute kinds `dispute_opened/_won/_lost/...`; `webhook_testing.sample_notification` | **Medium.** Reconcile with search, not webhooks. |
| Duplicate checking | Control Panel setting, 30-second window, same amount + order_id; applies to sales; refunds **UNVERIFIED** | Shows how narrow the rail's own duplicate guard is. |
| Refund rules | settled/settling only (91506, 91574 settling), partial refunds up to the total (91521), fully refunded (91512), void not possible (91504), refund of a credit (91505); docs advise 5–10 s between partial refunds | Already the basis of `rail_would_block`. |
| Agentic | PayPal's Agent Ready page: ChatGPT's Agentic Commerce Protocol through Braintree with single-use delegated tokens, allowance (`max_amount`, `currency`, `expires_at`) and `facilitator_details` on the transaction; refunds and returns not covered. No official Braintree MCP server. | **Medium–high for the pitch.** PayPal's own agentic flows cover buying, not refunds — the side Counterfoil covers. |

## PayPal REST (PP-acct, not reachable from Türkiye)

| Feature | Endpoint / tool | Relevance |
|---|---|---|
| Refund a capture | `POST /v2/payments/captures/{id}/refund` (body `amount`, `invoice_id`, `custom_id`, `note_to_payer`; header `PayPal-Request-Id`) | **High:** what Toolkit `create_refund` calls and what `toolkit.py` stands in for. |
| Refund rules | multiple partial refunds; `REFUND_AMOUNT_EXCEEDED` (422), `CAPTURE_FULLY_REFUNDED`, **`REFUND_NOT_ALLOWED_AFTER_180_DAYS`**, status `TRANSACTION_DISPUTED` | **High:** mirror these in the faked HTTP layer. |
| Agent Toolkit | 43 tools. Money-moving ones besides `create_refund`: `pay_order`, `accept_dispute_claim`, `record_refund_for_invoice`, `cancel_subscription`; no void or capture tool | **High:** `accept_dispute_claim` also moves money and should be gated. |
| PayPal MCP server | remote `mcp.sandbox.paypal.com`, local `npx @paypal/mcp` | Medium; tool list not published on the page (**UNVERIFIED** that it equals the Toolkit). |
| Disputes v1, Transaction Search v1 (`T1107` = refund), Webhooks (`PAYMENT.CAPTURE.REFUNDED`, `PAYMENT.REFUND.FAILED`, `CUSTOMER.DISPUTE.CREATED`) | — | Medium; Braintree equivalents above are the reachable ones. |
| Negative testing | `PayPal-Mock-Response` header | Low (PP-acct). |
| Orders v2, Vault v3, Subscriptions, Invoicing, Payouts, Partner, Venmo, Pay Later, Fastlane, Store Sync (US only) | — | Low for a refund gate. |

## Five to add before 12 Nov, ranked (all Braintree, all reachable from Türkiye)

1. **Line items on every sale + rail-side item check.** Write the order's lines onto the Braintree sale; on a refund, read them back with `transaction_line_item.find_all` and check the RMA's lines against what the rail says was sold. Today's checks all read the store's own records; this adds one that doesn't.
2. **`api_request_key` on refund and void**, derived from (order, RMA, amount). Test once in the sandbox that a repeated key does not refund twice; report the result either way.
3. **Open-dispute rule.** `transaction.disputes` / `dispute.search(transaction_id)`; BLOCK a refund on a disputed transaction. Demo with card `4023898493988028`.
4. **Store-wide refund sweep.** `transaction.search(refund == True, order_id …)` to list rail refunds the store doesn't know about (extends today's per-transaction `refunded_total`).
5. **Card + `testing.settle` beside mocked PayPal in the demo**, so the rail's own refusals are shown live and the "rail already refuses this, Counterfoil doesn't repeat it" split in the README is visible, not just written. Also: mirror `REFUND_NOT_ALLOWED_AFTER_180_DAYS` and `accept_dispute_claim` in the PayPal REST stand-in.

## Key sources
developer.paypal.com: `/braintree/docs/reference/request/transaction/{refund,sale,search}/python`, `/braintree/docs/reference/request/transaction-line-item/find-all/python`, `/braintree/docs/reference/general/{statuses,testing}`, `/braintree/docs/reference/general/webhooks/*`, `/braintree/docs/guides/paypal/testing-go-live/`, `/braintree/graphql/guides/transactions/`, `/braintree/graphql/integration_guides/idempotency/`, `/api/payments/v2/captures-refund`, `/checkout/refund-payment.md`, `/api/rest/reference/idempotency/`, `/api/rest/webhooks/event-names/`, `/ai-tools/mcp-server.md`, `/agent-ready/agentic-commerce-protocol`; github.com/paypal/agent-toolkit; github.com/braintree/braintree_python (CHANGELOG, `error_codes.py`).
