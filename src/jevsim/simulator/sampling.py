"""Sampling happens here, with the simulator's RNG, never inside an engine."""

import numpy as np


def sample_label(probs: dict[str, float], rng: np.random.Generator) -> str:
    labels = sorted(probs)  # fixed order so the same RNG state gives the same draw
    p = np.array([max(probs[k], 0.0) for k in labels], dtype=float)
    p = p / p.sum()
    return labels[int(rng.choice(len(labels), p=p))]
