"""On-disk cache of API responses, one JSON file per request.

The key includes the replicate index, so the n repeats of a Phase 1 cell are separate billed
calls the first time and all replay offline afterwards. Entries are written right after each
successful call, so a crash mid-batch never pays for the same call twice. No secrets are stored.
"""

import hashlib
import json
import os
from pathlib import Path


def cache_key(model: str, state, questions: dict, replicate: int) -> str:
    payload = json.dumps(
        {"model": model, "state": state, "questions": questions, "replicate": replicate},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class DiskCache:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict | None:
        p = self._path(key)
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def put(self, key: str, entry: dict) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry, ensure_ascii=False, indent=1))
        os.replace(tmp, p)

    def __contains__(self, key: str) -> bool:
        return self._path(key).exists()
