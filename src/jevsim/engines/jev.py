"""TypeSafe Jev behind the engine interface, with a disk cache and careful retries."""

import time
from datetime import datetime, timezone

from jevsim.cache import DiskCache, cache_key
from jevsim.engines.base import Decision
from jevsim.engines.transport import TransportError
from jevsim.probs import answer_to_probs
from jevsim.state_encoder import EncodedState

PINNED_MODEL = "jev-1.13.0"


class ModelVersionError(RuntimeError):
    pass


class JevEngine:
    name = "jev"

    def __init__(
        self,
        transport,
        cache: DiskCache,
        model: str = PINNED_MODEL,
        max_attempts: int = 4,
        backoff: float = 2.0,
        offline: bool = False,
    ):
        """offline=True only replays the cache and raises on a miss (for reproducing plots)."""
        self.transport = transport
        self.cache = cache
        self.model = model
        self.max_attempts = max_attempts
        self.backoff = backoff
        self.offline = offline

    def key(self, state: EncodedState, questions: dict, replicate: int = 0) -> str:
        return cache_key(self.model, state.text, questions, replicate)

    def decide(self, state: EncodedState, questions: dict, replicate: int = 0) -> Decision:
        key = self.key(state, questions, replicate)
        entry = self.cache.get(key)
        hit = entry is not None
        if entry is None:
            if self.offline:
                raise KeyError(f"cache miss in offline mode (key {key[:12]})")
            body = {"model": self.model, "state": state.text, "questions": questions}
            response = self._post_with_retries(body)
            if response.get("model") != self.model:
                raise ModelVersionError(
                    f"asked for {self.model}, got {response.get('model')}; refusing to mix versions"
                )
            entry = {
                "request": body,
                "replicate": replicate,
                "response": response,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            self.cache.put(key, entry)

        response = entry["response"]
        probs = {
            name: answer_to_probs(questions[name], answer)
            for name, answer in response["answers"].items()
        }
        meta = {
            "engine": self.name,
            "model": response["model"],
            "usage": response.get("usage"),
            "cache_hit": hit,
            "cache_key": key,
            "raw": response["answers"],
        }
        return Decision(probs=probs, meta=meta)

    def _post_with_retries(self, body: dict) -> dict:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self.transport.post(body)
            except TransportError as e:
                if not e.retryable or attempt == self.max_attempts:
                    raise
                time.sleep(self.backoff * 2 ** (attempt - 1))
        raise AssertionError("unreachable")
