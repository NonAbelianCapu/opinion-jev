"""Estimate tokens and cost before any batch, and refuse expensive batches without confirm=True.

Token estimate: characters of the JSON request body (state + questions) divided by
CHARS_PER_TOKEN. Calibrated on the Phase 0 request: 1,022 characters -> 516 billed input tokens.
Recalibrate from logged usage with calibrate_from_log() once real batches exist.
"""

import json

PRICE_PER_M_INPUT = 0.042  # USD per 1M input tokens; output is free
CHARS_PER_TOKEN = 1.98
CONFIRM_ABOVE_USD = 1.0


class BudgetError(RuntimeError):
    pass


def estimate_tokens(state_text: str, questions: dict, chars_per_token: float = CHARS_PER_TOKEN) -> int:
    body = json.dumps({"state": state_text, "questions": questions}, ensure_ascii=False)
    return int(len(body) / chars_per_token) + 1


def estimate(requests: list[tuple[str, dict]], chars_per_token: float = CHARS_PER_TOKEN) -> dict:
    tokens = sum(estimate_tokens(s, q, chars_per_token) for s, q in requests)
    return {"requests": len(requests), "input_tokens": tokens,
            "usd": tokens * PRICE_PER_M_INPUT / 1e6}


def check(est: dict, dry_run: bool = True, confirm: bool = False) -> bool:
    """Print the estimate. Returns True if the batch may run live."""
    print(f"[budget] {est['requests']} uncached requests, ~{est['input_tokens']:,} input tokens, "
          f"~${est['usd']:.4f}")
    if dry_run:
        print("[budget] dry run: nothing sent. Pass dry_run=False to call the API.")
        return False
    if est["usd"] > CONFIRM_ABOVE_USD and not confirm:
        raise BudgetError(f"estimated ${est['usd']:.2f} > ${CONFIRM_ABOVE_USD:.2f}; pass confirm=True")
    return True


def calibrate_from_log(records: list[dict]) -> float:
    """Chars per token from logged live calls (cache misses with usage)."""
    chars = tokens = 0
    for r in records:
        if r.get("cache_hit") or not r.get("usage"):
            continue
        chars += len(json.dumps({"state": r["state"], "questions": r["questions"]}, ensure_ascii=False))
        tokens += r["usage"]["input_tokens"]
    if tokens == 0:
        return CHARS_PER_TOKEN
    return chars / tokens
