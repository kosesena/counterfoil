"""Server-side configuration, read once from the environment. Nothing here is ever sent to the browser except the
public summary in `public()`; keys stay in the process.

Live mode is off unless a model is configured on purpose: DEMO_MODEL names a counterfoil.llm preset (its key comes
from that preset's env var), or LLM_BASE_URL + LLM_MODEL + LLM_API_KEY are all set. Falling back to a local Ollama
default, as run_eval does, would make a hosted demo look broken instead of clearly saying "replay only".
"""
from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass

from counterfoil.llm import LLMConfig, preset

BRAINTREE_VARS = ("BRAINTREE_MERCHANT_ID", "BRAINTREE_PUBLIC_KEY", "BRAINTREE_PRIVATE_KEY")


def _int(name: str, default: int, lo: int = 1) -> int:
    try:
        return max(lo, int(os.environ.get(name, default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    max_email_chars: int = 4000          # subject + body + HTML + attachment, all together
    max_turns: int = 6                   # same budgets as the evaluation, so live runs are comparable
    max_calls: int = 8
    rate_limit: int = 6                  # live runs per client IP per window
    rate_window_s: int = 600
    daily_llm_calls: int = 300           # every chat completion counts (Reader + each agent turn)
    max_concurrent: int = 2              # live runs in flight; more → 503 instead of a queue that times out
    llm_timeout_s: int = 60
    replay_source: str = ""              # results/<stem>.jsonl to replay by default; "" → the qwen2.5 run
    live: LLMConfig | None = None
    live_reason: str = "no model configured on the server (set DEMO_MODEL or LLM_BASE_URL/LLM_MODEL/LLM_API_KEY)"
    braintree: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        s = cls(
            max_email_chars=_int("DEMO_MAX_EMAIL_CHARS", cls.max_email_chars, 200),
            max_turns=_int("DEMO_MAX_TURNS", cls.max_turns),
            max_calls=_int("DEMO_MAX_CALLS", cls.max_calls),
            rate_limit=_int("DEMO_RATE_LIMIT", cls.rate_limit),
            rate_window_s=_int("DEMO_RATE_WINDOW_S", cls.rate_window_s),
            daily_llm_calls=_int("DEMO_DAILY_LLM_CALLS", cls.daily_llm_calls, 0),
            max_concurrent=_int("DEMO_MAX_CONCURRENT", cls.max_concurrent),
            llm_timeout_s=_int("DEMO_LLM_TIMEOUT_S", cls.llm_timeout_s),
            replay_source=os.environ.get("DEMO_REPLAY_SOURCE", ""),
            braintree=os.environ.get("BRAINTREE_ENVIRONMENT") == "sandbox" and all(os.environ.get(v) for v in BRAINTREE_VARS),
        )
        live, reason = live_config()
        if live is not None:
            live = dataclasses.replace(live, timeout=float(s.llm_timeout_s))
        return dataclasses.replace(s, live=live, live_reason=reason)

    def public(self) -> dict:
        """What the page may know: whether live mode works and which model, never where the key lives."""
        return {"live_enabled": self.live is not None, "live_model": self.live.model if self.live else None,
                "live_reason": "" if self.live else self.live_reason,
                "rail": "braintree-sandbox" if self.braintree else "fake",
                "limits": {"max_email_chars": self.max_email_chars, "max_turns": self.max_turns,
                           "max_calls": self.max_calls, "rate_limit": self.rate_limit,
                           "rate_window_s": self.rate_window_s, "daily_llm_calls": self.daily_llm_calls}}


def live_config() -> tuple[LLMConfig | None, str]:
    name = os.environ.get("DEMO_MODEL", "")
    if name:
        try:
            return preset(name), ""
        except (ValueError, RuntimeError) as exc:       # messages name the env var, never its value
            return None, str(exc)
    if all(os.environ.get(v) for v in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY")):
        return LLMConfig.from_env(), ""
    return None, Settings.live_reason
