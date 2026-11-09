"""Attempts written by people outside the project on the demo's "Write your own" tab, kept for later review.

The rows are not scored here: a pasted email has no ground truth. See docs/outside-red-team.md for how they are read.
Each attempt is printed to the server log, which outlives a restart, and kept in memory for the export route. The
address is reduced to a per-process keyed hash, so attempts can be grouped by person without storing who they were.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
from collections import deque
from datetime import UTC, datetime

LOG_PREFIX = "OUTSIDE_RUN "
MAX_KEPT = 5000
FIELDS = ("condition", "model", "status", "rail", "reader", "steps", "agent_stopped", "agent_final", "rail_money_calls")


class OutsideLog:
    def __init__(self, salt: bytes | None = None, emit=print):
        self.salt = salt or secrets.token_bytes(16)
        self.emit = emit
        self.rows: deque[dict] = deque(maxlen=MAX_KEPT)
        self.lock = threading.Lock()

    def _person(self, address: str) -> str:
        return hmac.new(self.salt, address.encode(), hashlib.sha256).hexdigest()[:16]

    def record(self, row: dict, address: str) -> None:
        """`row` must already be redacted: this goes to the log and the export as it is."""
        kept = {
            "at": datetime.now(UTC).isoformat(timespec="seconds"),
            "attempt": row["scenario"],
            "person": self._person(address),
            "email": row["email"],
            **{k: row.get(k) for k in FIELDS},
        }
        with self.lock:
            self.rows.append(kept)
        self.emit(LOG_PREFIX + json.dumps(kept, ensure_ascii=False), flush=True)

    def stats(self) -> dict:
        with self.lock:
            rows = list(self.rows)
        return {
            "runs": len(rows),
            "attempts": len({r["attempt"] for r in rows}),
            "people": len({r["person"] for r in rows}),
        }

    def export(self) -> str:
        with self.lock:
            return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.rows)
