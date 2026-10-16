import math

from jevsim.probs import answer_to_probs, binary_entropy, clip, expected_score, logit
from jevsim.questions import STANDARD_QUESTIONS


def test_clip_keeps_logit_finite_on_saturated_answers():
    assert math.isfinite(logit(0.0)) and math.isfinite(logit(1.0))
    assert clip(0.0) > 0 and clip(1.0) < 1


def test_entropy_of_saturated_answer_is_small_but_finite():
    assert 0 < binary_entropy(1.0) < 0.1
    assert abs(binary_entropy(0.5) - 1.0) < 1e-9


def test_real_response_maps_to_probabilities(real_response):
    answers = real_response["answers"]
    believe = answer_to_probs(STANDARD_QUESTIONS["believe"], answers["believe"])
    assert believe == {"believes": 0.0, "doubts": 1.0}  # the real API saturates
    share = answer_to_probs(STANDARD_QUESTIONS["share"], answers["share"])
    assert abs(sum(share.values()) - 1) < 1e-9
    trust = answer_to_probs(STANDARD_QUESTIONS["trust_source"], answers["trust_source"])
    assert abs(expected_score(trust) - answers["trust_source"]["score"]) < 0.02
