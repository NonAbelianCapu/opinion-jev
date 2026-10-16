"""Rewrite a message the way a given person would forward it, using an LLM through OpenRouter.

Jev decides *how* the message changes (the mutation type); this module only carries out that
decision. Rewrites are cached like Jev calls, keyed by model, prompt and replicate, so a run
replays offline with the same texts.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from jevsim.cache import DiskCache, cache_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_FILE = Path.home() / ".config" / "openrouter" / "api_key"
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"

MUTATION_INSTRUCTIONS = {
    "exaggerate": "EXAGGERATE: make the claim bigger, more alarming or more certain.",
    "soften": "SOFTEN: add doubt, or make the claim milder and less certain.",
    "add_detail": "ADD A DETAIL: add one specific detail (a number, a place, a date, a name of a "
                  "made-up neighbor) that was not in the message.",
    "change_source": "CHANGE THE SOURCE: say the claim comes from a different, more convincing "
                     "source (for example someone who works at the council).",
}

PROMPT = """You forward messages in a neighborhood chat group. Rewrite the message below the way this person would forward it.
Person: {persona}
Change to make: {instruction}
Keep it short (at most 2 sentences), keep the same topic, write in English, and output only the forwarded message, with no quotes or comments.

Message: "{message}\""""


def load_openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()
    try:
        from google.colab import userdata  # type: ignore

        key = userdata.get("OPENROUTER_API_KEY")
        if key:
            return key.strip()
    except Exception:
        pass
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip()
    raise RuntimeError("No OpenRouter key. Set OPENROUTER_API_KEY or add it as a Colab secret.")


class OpenRouterRewriter:
    def __init__(self, cache: DiskCache, model: str = DEFAULT_MODEL, temperature: float = 0.8,
                 offline: bool = False, api_key: str | None = None, max_attempts: int = 4):
        self.cache = cache
        self.model = model
        self.temperature = temperature
        self.offline = offline
        self._key = api_key
        self.max_attempts = max_attempts
        self._client = None

    def prompt(self, message: str, mutation: str, persona: str) -> str:
        return PROMPT.format(persona=persona, instruction=MUTATION_INSTRUCTIONS[mutation],
                             message=message)

    def rewrite(self, message: str, mutation: str, persona: str, replicate: str = "0") -> dict:
        """Returns {"text", "cache_hit", "usage"}. 'verbatim' returns the message unchanged."""
        if mutation == "verbatim":
            return {"text": message, "cache_hit": True, "usage": None}
        prompt = self.prompt(message, mutation, persona)
        key = cache_key(f"openrouter:{self.model}:t{self.temperature}", prompt, {}, replicate)
        entry = self.cache.get(key)
        if entry is not None:
            return {"text": entry["text"], "cache_hit": True, "usage": entry.get("usage")}
        if self.offline:
            raise KeyError(f"rewrite cache miss in offline mode (key {key[:12]})")
        data = self._post(prompt)
        text = data["choices"][0]["message"]["content"].strip().strip('"').strip()
        if not text:
            raise RuntimeError(f"{self.model} returned an empty rewrite")
        self.cache.put(key, {"prompt": prompt, "model": self.model, "text": text,
                             "usage": data.get("usage"), "replicate": replicate,
                             "fetched_at": datetime.now(timezone.utc).isoformat()})
        return {"text": text, "cache_hit": False, "usage": data.get("usage")}

    def _post(self, prompt: str) -> dict:
        if self._client is None:
            self._key = self._key or load_openrouter_key()
            self._client = httpx.Client(timeout=60)
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200, "temperature": self.temperature,
                "reasoning": {"enabled": False}}
        for attempt in range(1, self.max_attempts + 1):
            try:
                r = self._client.post(OPENROUTER_URL, json=body,
                                      headers={"Authorization": f"Bearer {self._key}"})
                if r.status_code == 200:
                    return r.json()
                if r.status_code != 429 and r.status_code < 500:
                    raise RuntimeError(f"OpenRouter HTTP {r.status_code}: {r.text[:300]}")
            except httpx.HTTPError:
                if attempt == self.max_attempts:
                    raise
            time.sleep(2 ** attempt)
        raise RuntimeError("OpenRouter: out of retries")


class FakeRewriter:
    """Offline stand-in for tests: tags the text with the mutation instead of calling an LLM."""

    def __init__(self):
        self.calls = 0

    def rewrite(self, message: str, mutation: str, persona: str, replicate: str = "0") -> dict:
        if mutation == "verbatim":
            return {"text": message, "cache_hit": True, "usage": None}
        self.calls += 1
        return {"text": f"{message} [{mutation}]", "cache_hit": False, "usage": None}

