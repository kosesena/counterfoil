"""OpenAI-compatible chat client. Local Ollama by default; Vultr Serverless Inference uses the same API
(LLM_BASE_URL=https://api.vultrinference.com/v1, LLM_API_KEY=..., LLM_MODEL=<a tool-calling model>)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str
    temperature: float = 0.0
    seed: int | None = 7
    timeout: float = 300.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            base_url=os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1"),
            model=os.environ.get("LLM_MODEL", "qwen2.5-8k"),
            api_key=os.environ.get("LLM_API_KEY", "ollama"),       # Ollama ignores the key
        )


class LLM:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        self.client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key, timeout=self.config.timeout)

    def chat(self, messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False):
        kw = {"model": self.config.model, "messages": messages, "temperature": self.config.temperature}
        if self.config.seed is not None:
            kw["seed"] = self.config.seed
        if tools:
            kw["tools"] = tools
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(**kw).choices[0].message
