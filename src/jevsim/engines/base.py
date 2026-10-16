"""The engine interface. Engines return probabilities; they never sample."""

from dataclasses import dataclass, field
from typing import Protocol

from jevsim.state_encoder import EncodedState


@dataclass
class Decision:
    probs: dict[str, dict[str, float]]  # question name -> {label: probability}
    meta: dict = field(default_factory=dict)  # model version, usage, cache hit, raw answers


class Engine(Protocol):
    name: str

    def decide(self, state: EncodedState, questions: dict, replicate: int = 0) -> Decision:
        """replicate distinguishes repeated calls on the same state (Jev is not idempotent)."""
        ...
