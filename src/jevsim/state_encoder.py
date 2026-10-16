"""Turn (person, message, source, neighbors) into what an engine sees.

encode() builds both views from the same inputs in one place: the text that Jev reads and the
numbers that the stand-in rule needs. Every engine gets the same EncodedState.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

from jevsim.probs import clip

Direction = Literal["for", "against"]

# Shift of the stand-in's starting belief when the message agrees / disagrees with the person.
AGREEMENT_SHIFT = 0.15


@dataclass(frozen=True)
class Person:
    name: str
    prior_belief: float  # initial P(believe) for a message like this, 0..1
    stance: Optional[Direction] = None  # the person's view on the topic, None = no view


@dataclass(frozen=True)
class Source:
    description: str  # e.g. "an anonymous account in the neighborhood chat group"
    trust: float  # stand-in trust, 0..100


@dataclass(frozen=True)
class Message:
    text: str
    emotion: float  # stand-in emotion, 0..100
    direction: Direction = "for"  # which side of the topic the message supports
    # How a person holding each view is described, e.g. {"for": "thinks the council should be
    # stricter about bins", "against": "thinks the council already has too many rules"}.
    stance_phrases: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EncodedState:
    text: str
    features: dict  # numbers for the stand-in: belief, trust, emotion, exposures, agreement


def persona_sentence(prior: float) -> str:
    """Bin the numeric prior into a sentence Jev can read."""
    if prior < 0.25:
        return "usually doubts neighborhood rumors"
    if prior < 0.4:
        return "is cautious about neighborhood rumors but sometimes believes them"
    return "is fairly open to believing neighborhood rumors"


def agreement(person: Person, message: Message) -> Literal["agrees", "disagrees", "unrelated"]:
    if person.stance is None:
        return "unrelated"
    return "agrees" if person.stance == message.direction else "disagrees"


def encode(
    person: Person,
    message: Message,
    source: Source,
    shared_by: int = 0,
    times_seen: int = 1,
    belief: float | None = None,
) -> EncodedState:
    """shared_by: contacts known to have shared it. times_seen: exposures so far, this one included.
    belief: the stand-in's current belief, when it has moved away from the prior during a run.
    The text only describes the person's prior disposition, which does not change."""
    lines = [f"Person: {person.name}, who {persona_sentence(person.prior_belief)}."]
    if person.stance is not None and person.stance in message.stance_phrases:
        lines.append(f"{person.name} {message.stance_phrases[person.stance]}.")
    lines.append(f"Source: {source.description}.")
    lines.append(f'Message: "{message.text}"')
    if shared_by > 0:
        noun = "contact" if shared_by == 1 else "contacts"
        lines.append(f"Context: {shared_by} of {person.name}'s {noun} shared this message.")
    if times_seen > 1:
        lines.append(f"{person.name} has now seen this message {times_seen} times.")

    agree = agreement(person, message)
    shift = {"agrees": AGREEMENT_SHIFT, "disagrees": -AGREEMENT_SHIFT, "unrelated": 0.0}[agree]
    features = {
        # Agreement shifts the starting point once; a belief carried over from earlier exposures
        # already includes it.
        "belief": clip(person.prior_belief + shift) if belief is None else clip(belief),
        "trust": source.trust,
        "emotion": message.emotion,
        "exposures": max(1, shared_by),
        "agreement": agree,
    }
    return EncodedState(text="\n".join(lines), features=features)
