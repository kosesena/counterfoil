"""Saved evaluation runs (results/*.jsonl) as the demo's zero-key, zero-cost mode.

A replay returns the row exactly as run_eval wrote it: the Reader's hand-off, every tool call with the gate's
decision and the rail state, and the score. Nothing is re-run, so what a judge sees is what was measured.
"""

from __future__ import annotations

import json
from pathlib import Path

# Runs from this date on use the current gate (their .meta.json files name the gate commit); the README's results and
# the dashboard count only these. Earlier files stay listed, marked as the previous gate.
CURRENT_GATE_SINCE = "2026-10-25"


class Replays:
    def __init__(self, folder: Path, default: str = ""):
        self.rows: dict[tuple[str, str, str], dict] = {}
        self.sources: dict[str, dict] = {}
        for path in sorted(folder.glob("*.jsonl")):
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not rows:
                continue
            for r in sorted(rows, key=lambda r: r.get("repeat", 0), reverse=True):  # repeat 0 wins
                self.rows[(path.stem, r["scenario"], r["condition"])] = r
            self.sources[path.stem] = {
                "id": path.stem,
                "model": rows[0].get("model", ""),
                "scenarios": sorted({r["scenario"] for r in rows}),
                "gate": "current" if path.stem[:10] >= CURRENT_GATE_SINCE else "previous",
            }
        current = [s for s, v in self.sources.items() if v["gate"] == "current"]
        qwen = next((s for s in current if self.sources[s]["model"].startswith("qwen2.5") and "-dev-r3-" in s), None)
        self.default = default if default in self.sources else qwen or next(iter(current or self.sources), "")

    def get(self, source: str, scenario_id: str, condition: str) -> dict | None:
        row = self.rows.get((source or self.default, scenario_id, condition))
        return json.loads(json.dumps(row)) if row else None  # callers may annotate their copy

    def available(self, scenario_id: str) -> list[str]:
        return [s for s, v in self.sources.items() if scenario_id in v["scenarios"]]
