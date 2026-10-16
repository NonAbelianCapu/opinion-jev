import json
from pathlib import Path

import pytest

from jevsim import Message, Person, Source, encode
from jevsim.cache import DiskCache

PHASE0 = Path(__file__).resolve().parents[1] / "results" / "phase0"


@pytest.fixture
def real_response():
    return json.loads((PHASE0 / "response_1.json").read_text())


@pytest.fixture
def cache(tmp_path):
    return DiskCache(tmp_path / "cache")


@pytest.fixture
def state():
    msg = Message(
        text="Starting next month the council will fine anyone who leaves bins out after 8am.",
        emotion=20,
        direction="for",
        stance_phrases={"for": "thinks the council should be stricter about bins",
                        "against": "thinks the council already has too many rules"},
    )
    person = Person(name="Marta", prior_belief=0.3, stance="against")
    source = Source(description="an anonymous account in the neighborhood chat group", trust=25)
    return encode(person, msg, source, shared_by=3)
