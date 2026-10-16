"""Turn raw engine answers into probability vectors, and keep them away from 0 and 1.

Jev rounds probabilities to two decimals and often returns exactly 0.0 or 1.0. A logit of
those is infinite, so every probability that feeds a logit or an entropy goes through clip().
"""

import math

EPS = 0.005


def clip(p: float, eps: float = EPS) -> float:
    return min(max(p, eps), 1.0 - eps)


def logit(p: float) -> float:
    p = clip(p)
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def binary_entropy(p: float) -> float:
    """Entropy in bits. Saturated answers (0.0/1.0 from Jev) give ~0.05 bits after clipping,
    so a run where Jev is always certain shows near-zero uncertainty by construction."""
    p = clip(p)
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def answer_to_probs(question: dict, answer: dict) -> dict[str, float]:
    """Map one API answer to {label: probability}, whatever the question type."""
    kind = question["type"]
    if kind == "choice":
        return {k: float(v) for k, v in answer["probabilities"].items()}
    if kind == "score":
        return {str(k): float(v) for k, v in answer["probabilities"].items()}
    if kind == "noul":
        p = float(answer["noul"])
        return {"true": p, "false": 1.0 - p}
    raise ValueError(f"unsupported question type {kind!r}")


def expected_score(probs: dict[str, float]) -> float:
    total = sum(probs.values()) or 1.0
    return sum(int(k) * v for k, v in probs.items()) / total
