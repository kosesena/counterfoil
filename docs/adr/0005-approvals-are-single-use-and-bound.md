# 0005 · Human approvals are single-use, time-limited and bound to the exact call

**Status:** accepted · 2026-10-23 (from the Codex review, finding 4)

## Context
"Hold for a human" is only safe if what the human approves is what executes. An approval that can be replayed, or
reused with different arguments, or used after the refund state changed, turns the human into a rubber stamp.

## Decision
An approval is single-use and expires after 30 minutes. It is bound to a fingerprint of session, tool and exact
arguments, and to the refund state the human saw. On approval every check runs again. Any new finding blocks it.

## Consequences
- After a blocked attempt, every later money call in that session is held. In the demo, even the correct $40 refund
  waits for the manager, and only her approval sends it to Braintree.
- The gate is a little slower for genuine edge cases, by design: the store's policy decides what needs a person.
