"""How requests reach TypeSafe: a real HTTP transport and a fake one for offline tests."""

import hashlib
import json
import os
from pathlib import Path

import httpx

API_URL = "https://api.typesafe.ai/v1/systemone"
KEY_FILE = Path.home() / ".config" / "typesafe" / "api_key"


class TransportError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status

    @property
    def retryable(self) -> bool:
        # No status means the request never got an answer (network error, timeout).
        return self.status is None or self.status == 429 or self.status >= 500


def load_api_key() -> str:
    """TYPESAFE_API_KEY env var, then Colab secrets, then ~/.config/typesafe/api_key."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key.strip()
    try:
        from google.colab import userdata  # type: ignore

        key = userdata.get("TYPESAFE_API_KEY")
        if key:
            return key.strip()
    except Exception:
        pass
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip()
    raise RuntimeError(
        "No TypeSafe API key. Set TYPESAFE_API_KEY, add it as a Colab secret, "
        f"or write it to {KEY_FILE}."
    )


class HttpTransport:
    def __init__(self, api_key: str | None = None, url: str = API_URL, timeout: float = 60.0):
        self._key = api_key or load_api_key()
        self.url = url
        self._client = httpx.Client(timeout=timeout)

    def post(self, body: dict) -> dict:
        try:
            r = self._client.post(
                self.url, json=body, headers={"Authorization": f"Bearer {self._key}"}
            )
        except httpx.HTTPError as e:
            raise TransportError(f"{type(e).__name__}: {e}") from e
        if r.status_code != 200:
            raise TransportError(f"HTTP {r.status_code}: {r.text[:300]}", status=r.status_code)
        return r.json()


def _unit(*parts: str) -> float:
    h = hashlib.sha256("\x1f".join(parts).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64


class FakeTransport:
    """Answers like the real API: same shape, two-decimal rounding, saturated values allowed.

    Values are a deterministic function of (state, question, replicate salt), so tests are
    reproducible. Pass `failures` (a list of TransportError) to make the first calls fail.
    """

    def __init__(self, model: str = "jev-1.13.0", failures: list | None = None):
        self.model = model
        self.calls: list[dict] = []
        self.failures = list(failures or [])

    def post(self, body: dict) -> dict:
        self.calls.append(body)
        if self.failures:
            raise self.failures.pop(0)
        state = body["state"] if isinstance(body["state"], str) else json.dumps(body["state"])
        salt = str(len(self.calls))  # differs per call, like the real non-idempotent API
        answers = {}
        for name, q in body["questions"].items():
            u = _unit(state, name)
            jitter = (_unit(state, name, salt) - 0.5) * 0.02
            if q["type"] == "choice":
                labels = list(q["criteria"])
                p = round(min(max(u + jitter, 0.0), 1.0), 2)
                if u > 0.9:
                    p = 1.0  # the real API often saturates
                probs = {labels[0]: p, labels[1]: round(1 - p, 2)}
                for extra in labels[2:]:
                    probs[extra] = 0.0
                best = max(probs, key=probs.get)
                answers[name] = {"type": "choice", "choice": best, "confidence": probs[best],
                                 "probabilities": probs}
            elif q["type"] == "score":
                n = len(q["criteria"])
                level = int(u * n) % n
                probs = {str(i): 0.0 for i in range(n)}
                probs[str(level)] = 0.8
                probs[str(max(level - 1, 0)) if level else str(min(1, n - 1))] += 0.2
                score = round(sum(int(k) * v for k, v in probs.items()), 2)
                answers[name] = {"type": "score", "score": score, "confidence": 0.8,
                                 "legend": {str(i): c for i, c in enumerate(q["criteria"])},
                                 "probabilities": probs}
            elif q["type"] == "noul":
                answers[name] = {"type": "noul", "noul": round(min(max(u + jitter, 0), 1), 2)}
            else:
                raise ValueError(q["type"])
        return {"model": self.model, "answers": answers,
                "usage": {"input_tokens": len(json.dumps(body)) // 2, "output_tokens": 60}}
