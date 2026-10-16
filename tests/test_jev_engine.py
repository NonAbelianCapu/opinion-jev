import pytest

from jevsim import STANDARD_QUESTIONS
from jevsim.batch import run_batch
from jevsim.budget import BudgetError, check, estimate
from jevsim.engines import FakeTransport, JevEngine
from jevsim.engines.jev import ModelVersionError
from jevsim.engines.transport import TransportError
from jevsim.logger import JsonlLogger, read_jsonl


def test_cache_hit_on_second_call(cache, state):
    t = FakeTransport()
    eng = JevEngine(t, cache, backoff=0)
    a = eng.decide(state, STANDARD_QUESTIONS)
    b = eng.decide(state, STANDARD_QUESTIONS)
    assert len(t.calls) == 1 and not a.meta["cache_hit"] and b.meta["cache_hit"]
    assert a.probs == b.probs


def test_replicates_are_separate_calls(cache, state):
    t = FakeTransport()
    eng = JevEngine(t, cache, backoff=0)
    for r in range(5):
        eng.decide(state, STANDARD_QUESTIONS, replicate=r)
    assert len(t.calls) == 5
    for r in range(5):  # and all replay from cache
        assert eng.decide(state, STANDARD_QUESTIONS, replicate=r).meta["cache_hit"]
    assert len(t.calls) == 5


def test_offline_mode_never_calls(cache, state):
    eng = JevEngine(FakeTransport(), cache, offline=True)
    with pytest.raises(KeyError):
        eng.decide(state, STANDARD_QUESTIONS)


def test_version_mismatch_is_an_error(cache, state):
    eng = JevEngine(FakeTransport(model="jev-1.14.0"), cache, backoff=0)
    with pytest.raises(ModelVersionError):
        eng.decide(state, STANDARD_QUESTIONS)


def test_retries_only_retryable_errors(cache, state):
    t = FakeTransport(failures=[TransportError("boom", status=503), TransportError("net")])
    JevEngine(t, cache, backoff=0).decide(state, STANDARD_QUESTIONS)
    assert len(t.calls) == 3

    t = FakeTransport(failures=[TransportError("bad request", status=422)])
    with pytest.raises(TransportError):
        JevEngine(t, cache, backoff=0).decide(state, STANDARD_QUESTIONS, replicate=1)
    assert len(t.calls) == 1


def test_budget_requires_confirm_above_one_dollar():
    big = {"requests": 10**6, "input_tokens": 50 * 10**6, "usd": 2.1}
    with pytest.raises(BudgetError):
        check(big, dry_run=False)
    assert check(big, dry_run=False, confirm=True)
    assert not check(big)  # dry run by default


def test_estimate_is_close_to_phase0_usage(real_response):
    import json
    from pathlib import Path
    req = json.loads((Path(__file__).resolve().parents[1] / "results/phase0/request.json").read_text())
    est = estimate([(req["state"], req["questions"])])
    assert abs(est["input_tokens"] - real_response["usage"]["input_tokens"]) < 15


def test_batch_dry_run_sends_nothing_and_logs_live_runs(cache, state, tmp_path):
    t = FakeTransport()
    eng = JevEngine(t, cache, backoff=0)
    items = [{"state": state, "replicate": r, "cell": "c1"} for r in range(3)]
    assert run_batch(eng, items, STANDARD_QUESTIONS) == [] and t.calls == []
    log = JsonlLogger(tmp_path / "log.jsonl")
    run_batch(eng, items, STANDARD_QUESTIONS, logger=log, dry_run=False)
    recs = read_jsonl(tmp_path / "log.jsonl")
    assert len(recs) == 3 and all(r["model"] == "jev-1.13.0" and r["cell"] == "c1" for r in recs)
    assert "Authorization" not in (tmp_path / "log.jsonl").read_text()
