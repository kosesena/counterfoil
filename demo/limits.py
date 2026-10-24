"""Abuse limits for live mode. In-process and in-memory on purpose: the demo is one small instance, and a restart
resetting the counters is acceptable. The daily cap is the backstop for everything the per-IP limit misses
(spoofed or rotating addresses)."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from datetime import UTC, datetime


class BudgetExhausted(RuntimeError):
    pass


class RateLimiter:
    """Sliding window per key. Old keys are dropped so the table cannot grow without bound."""

    def __init__(self, limit: int, window_s: float, clock=time.monotonic, max_keys: int = 10_000):
        self.limit, self.window, self.clock, self.max_keys = limit, window_s, clock, max_keys
        self.hits: dict[str, deque] = {}
        self.lock = threading.Lock()

    def retry_after(self, key: str) -> float:
        """0 → allowed (and counted); otherwise seconds until the oldest hit leaves the window."""
        now = self.clock()
        with self.lock:
            q = self.hits.setdefault(key, deque())
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return round(self.window - (now - q[0]), 1)
            q.append(now)
            if len(self.hits) > self.max_keys:
                for k in [k for k, v in self.hits.items() if not v or now - v[-1] >= self.window]:
                    del self.hits[k]
            return 0.0


class DailyBudget:
    """Counts LLM calls per UTC day across all clients."""

    def __init__(self, limit: int, today=lambda: datetime.now(UTC).date()):
        self.limit, self.today = limit, today
        self.day, self.used = today(), 0
        self.lock = threading.Lock()

    def _roll(self):
        if self.today() != self.day:
            self.day, self.used = self.today(), 0

    def remaining(self) -> int:
        with self.lock:
            self._roll()
            return max(0, self.limit - self.used)

    def take(self) -> None:
        with self.lock:
            self._roll()
            if self.used >= self.limit:
                raise BudgetExhausted("the demo's daily LLM budget is used up; replay mode still works")
            self.used += 1


class MeteredLLM:
    """Wraps counterfoil.llm.LLM: every chat completion is charged to the daily budget before it is sent. A run
    that hits the cap mid-way ends the way any model error does (recorded in the row, not raised)."""

    def __init__(self, llm, budget: DailyBudget):
        self.llm, self.budget, self.config = llm, budget, llm.config

    def chat(self, *a, **kw):
        self.budget.take()
        return self.llm.chat(*a, **kw)


class LRU(OrderedDict):
    """Reader hand-offs, keyed by scenario id, so the three conditions of one email share one Reader output
    (the evaluation's paired comparison) and a judge clicking through conditions does not pay for the Reader thrice."""

    def __init__(self, size: int = 64):
        super().__init__()
        self.size = size

    def __getitem__(self, key):
        self.move_to_end(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > self.size:
            self.popitem(last=False)
