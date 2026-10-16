"""The hand-written logistic rule from the interactive widget.

share_p = sigmoid(-1.6 + 2.2 * (2*belief - 1) + 0.04 * emotion)          emotion in 0..100
belief' = sigmoid(logit(belief) + (trust/100) * 2.2 * min(exposures, 3))   trust in 0..100

It reads EncodedState.features, never the text. It is deterministic, so replicate is ignored.
"""

from jevsim.engines.base import Decision
from jevsim.probs import logit, sigmoid
from jevsim.state_encoder import EncodedState


def updated_belief(belief: float, trust: float, exposures: int) -> float:
    return sigmoid(logit(belief) + (trust / 100.0) * 2.2 * min(exposures, 3))


def share_probability(belief: float, emotion: float) -> float:
    return sigmoid(-1.6 + 2.2 * (2 * belief - 1) + 0.04 * emotion)


def trust_levels(trust: float, n_levels: int) -> dict[str, float]:
    """Spread trust (0..100) over score levels 0..n-1, split between the two nearest levels."""
    x = trust / 100.0 * (n_levels - 1)
    lo = int(x)
    hi = min(lo + 1, n_levels - 1)
    w = x - lo
    probs = {str(i): 0.0 for i in range(n_levels)}
    probs[str(lo)] += 1.0 - w
    probs[str(hi)] += w
    return probs


# Fixed mutation odds for the stand-in: it cannot read text, so how it rewrites does not depend
# on the person or the message.
STANDIN_MUTATION = {"verbatim": 0.5, "exaggerate": 0.2, "soften": 0.1, "add_detail": 0.1,
                    "change_source": 0.1}


class StandInEngine:
    name = "standin"

    def decide(self, state: EncodedState, questions: dict, replicate: int = 0) -> Decision:
        f = state.features
        belief = updated_belief(f["belief"], f["trust"], f["exposures"])
        probs: dict[str, dict[str, float]] = {}
        for qname, q in questions.items():
            if qname == "believe":
                probs[qname] = {"believes": belief, "doubts": 1.0 - belief}
            elif qname == "believe_p":
                probs[qname] = {"true": belief, "false": 1.0 - belief}
            elif qname == "mutation":
                probs[qname] = dict(STANDIN_MUTATION)
            elif qname == "share":
                p = share_probability(belief, f["emotion"])
                probs[qname] = {"true": p, "false": 1.0 - p}
            elif qname == "trust_source":
                probs[qname] = trust_levels(f["trust"], len(q["criteria"]))
            else:
                raise KeyError(f"stand-in has no rule for question {qname!r}")
        return Decision(probs=probs, meta={"engine": self.name, "model": "standin-v1"})
