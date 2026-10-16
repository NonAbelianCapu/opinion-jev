"""Append-only JSONL log of every decision: state, questions, probabilities, version, cache use.

Every plot is rebuilt from these files. Request headers (and so the API key) are never logged.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from jevsim.engines.base import Decision
from jevsim.state_encoder import EncodedState


class JsonlLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, state: EncodedState, questions: dict, decision: Decision, **tags) -> dict:
        record = {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "engine": decision.meta.get("engine"),
            "model": decision.meta.get("model"),
            "cache_hit": decision.meta.get("cache_hit"),
            "cache_key": decision.meta.get("cache_key"),
            "usage": decision.meta.get("usage"),
            "state": state.text,
            "features": state.features,
            "questions": questions,
            "probs": decision.probs,
            **tags,
        }
        with self.path.open("a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record


def read_jsonl(path: str | Path) -> list[dict]:
    with Path(path).open() as f:
        return [json.loads(line) for line in f if line.strip()]
