# Who needs this: public evidence (2 Nov 2026)

We could not interview merchants for this project, so the case for a real audience rests on public, checkable
sources. Each claim below was read on the source page on 2 Nov 2026; the strength of each source is stated.

## 1. AI support agents already move refund money

| Source | What it says | Strength |
|---|---|---|
| [Intercom, "Fin Actions templates"](https://intercom.com/help/en/articles/9909996-fin-actions-templates) | Fin's ready-made action templates include **Create Shopify Refund** ("refund items or shipping on an order") and Stripe **Refund charge (full)** / **Refund charge (partial)**. | Vendor's own help center |
| [Gorgias, "AI Agent Actions: make changes to Shopify orders"](https://docs.gorgias.com/en-US/ai-agent-action-cancel-an-order-in-shopify-757792) | When AI Agent cancels an unfulfilled order "the shopper gets a refund for the full amount paid"; when it removes an item it "refunds the shopper the amount of the removed item". The page names no approval step or amount cap. | Vendor's own docs |
| [PayPal Agent Toolkit README](https://github.com/paypal/agent-toolkit) | Gives an agent `create_refund` ("Process a refund for a captured payment"), `get_refund`, and dispute tools including `accept_dispute_claim`. | PayPal's official repository |

So the audience is concrete: merchants on Shopify, Stripe or PayPal who turn on an AI support agent with a refund
action. The refund decision moves from a person to the agent, and the agent reads text the customer wrote.

## 2. Merchants already fight return and refund abuse by hand

| Source | What it says | Strength |
|---|---|---|
| [Shopify Community, "Small item return fraud"](https://community.shopify.com/t/small-item-return-fraud/353188/1) (29 Aug 2024) | A merchant got 8 near-identical return requests for one sub-$25 product, then 10 more for another, and raised the restocking fee to 20% on every order to stop it. | One merchant's account |
| [Shopify Community, "Possible fraud: the client got an empty box"](https://community.shopify.com/t/possible-fraud-the-client-got-an-empty-box/122927) (22 May 2022) | A customer reported a delivered €200 parcel arrived empty 15 days later, though the carrier confirmed delivery; a reply warns a chargeback "will cost you more than the original amount". | One merchant's account |
| [Shopify Community, "Returned order shipment fraud?"](https://community.shopify.com/t/returned-order-shipment-fraud/420086) (19 Jun 2025) | A merchant suspects a buyer covered the return label's address to claim a refund and keep the parcel; the reply recommends a stricter returns portal with "manual approval only" for return requests. | One merchant's account, one vendor reply |
| [Appriss Retail and Deloitte, 2024 Consumer Returns report](https://apprissretail.com/resources/2024-consumer-returns-report/) | US retailers lost an estimated $103B to fraudulent returns and claims in 2024. | Industry report ([notes](kaynaklar.md)) |

The merchants' own fix is to check every return by hand before money moves. Counterfoil does the check against the
return record automatically and leaves a person only the cases that don't match.

## 3. Support bots are already talked into promises

| Source | What it says | Strength |
|---|---|---|
| *Moffatt v. Air Canada*, 2024 BCCRT 149 | The airline was held responsible for a refund policy its chatbot invented. | Tribunal decision ([notes](kaynaklar.md)) |
| [Reinforce Labs red test, via Vibe Graveyard](https://vibegraveyard.ai/story/reinforce-labs-red-team-live-support-chatbots-policy-violations/) (1 Oct 2026) | 11 of 14 live support chatbots made unapproved commitments such as refunds or warranties. | The testing firm's own account; companies unnamed |
| [UK shop's after-hours bot, via Vibe Graveyard](https://vibegraveyard.ai/story/uk-chatbot-80-percent-discount-refund/) (Feb 2026) | The bot was flattered into inventing discount codes up to 80% off. | The owner's account |

**Not found:** a verified, named case of an AI agent that moved refund money because of an instruction in a
customer's message. The risk is documented at the promise level; section 1 shows agents now hold the refund tool.

## What this does not show

- How many merchants have turned refund actions on, or how often those agents are attacked.
- That Counterfoil would have stopped any specific incident above; our numbers come from our own 14 attacks.
