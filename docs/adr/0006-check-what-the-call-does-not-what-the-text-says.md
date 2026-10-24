# 0006 · Check what the call would do, not what the text looks like

**Status:** accepted · 2026-10-23

## Context
The obvious defence is to look for injection-looking text ("ignore previous instructions", hidden HTML) and refuse it.
In the author's thesis prototype, a pattern list of instruction phrases caught 0 of 36 attack variations written by a
second model. The checks that held were the ones that looked at the action: permission, critical fields and business
rules.

## Decision
Counterfoil does not classify text. It evaluates the effect of each call: which order, which RMA, how much in total,
whose payment method, which tool. Then it compares that effect with the record.

## Consequences
- The gate is indifferent to the attack's wording, language or encoding, and the same rules cover attacks not yet
  written.
- It cannot stop an attack that produces a call the records allow, for example a refund exactly equal to a genuine
  RMA. That is a correct refund by the store's own definition.
- A text classifier (such as Vultr's content-safety model) can still be added as an early warning. It would not be the
  control.
