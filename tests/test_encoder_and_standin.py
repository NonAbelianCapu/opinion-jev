from jevsim import STANDARD_QUESTIONS, Message, Person, Source, encode
from jevsim.engines import StandInEngine
from jevsim.engines.standin import share_probability, updated_belief


def test_encoder_text_and_features(state):
    assert "Marta" in state.text and "anonymous account" in state.text
    assert "3 of Marta's contacts" in state.text
    assert state.features["agreement"] == "disagrees"
    assert abs(state.features["belief"] - 0.15) < 1e-9
    assert state.features["exposures"] == 3


def test_unrelated_when_person_has_no_stance():
    s = encode(Person("Ana", 0.3), Message("x", 50), Source("the council", 75))
    assert s.features["agreement"] == "unrelated" and "Context" not in s.text


def test_standin_matches_widget_formulas(state):
    d = StandInEngine().decide(state, STANDARD_QUESTIONS)
    b = updated_belief(0.15, 25, 3)
    assert abs(d.probs["believe"]["believes"] - b) < 1e-12
    assert abs(d.probs["share"]["true"] - share_probability(b, 20)) < 1e-12
    assert abs(sum(d.probs["trust_source"].values()) - 1) < 1e-12


def test_more_trust_means_more_belief():
    assert updated_belief(0.3, 75, 1) > updated_belief(0.3, 25, 1)
    assert updated_belief(0.3, 50, 5) == updated_belief(0.3, 50, 3)  # exposures capped at 3
