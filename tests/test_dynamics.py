from jevsim import Message, Source
from jevsim.engines import FakeTransport, JevEngine, StandInEngine
from jevsim.rewriter import FakeRewriter
from jevsim.simulator.dynamics import Scenario, simulate

SCENARIO = Scenario(
    message=Message("The council will fine anyone who leaves bins out after 8am.", 50, "for",
                    {"for": "thinks the council should be stricter about bins",
                     "against": "thinks the council already has too many rules"}),
    origin=Source("an anonymous account in the neighborhood chat group", 25),
)


def test_standin_run_is_reproducible_and_spreads():
    a = simulate(StandInEngine(), FakeRewriter(), SCENARIO, graph_seed=1, run_seed=3)
    b = simulate(StandInEngine(), FakeRewriter(), SCENARIO, graph_seed=1, run_seed=3)
    assert a["events"] == b["events"] and a["metrics"] == b["metrics"]
    assert a["metrics"][-1]["shared"] > 1 / 64
    # every non-original variant points to an existing parent with a lower id
    for v in a["variants"][1:]:
        assert v["parent"] is not None and v["parent"] < v["id"]
    # nodes share at most once
    shares = [e["node"] for e in a["events"] if e.get("shares") or e.get("kind") == "seed"]
    assert len(shares) == len(set(shares))


def test_jev_run_needs_explicit_live_flag(cache):
    eng = JevEngine(FakeTransport(), cache, backoff=0)
    assert simulate(eng, FakeRewriter(), SCENARIO) is None  # dry run
    assert eng.transport.calls == []
    out = simulate(eng, FakeRewriter(), SCENARIO, scorer=eng, dry_run=False)
    assert out["variants"][0]["emotion"] is not None
    n_calls = len(eng.transport.calls)
    offline = JevEngine(FakeTransport(), cache, offline=True)
    replay = simulate(offline, FakeRewriter(), SCENARIO, scorer=offline)
    assert replay["events"] == out["events"] and offline.transport.calls == []
    assert n_calls > 0


def test_html_page_embeds_runs():
    from jevsim.viz import build_html
    run = simulate(StandInEngine(), FakeRewriter(), SCENARIO, graph_seed=1, run_seed=3)
    html = build_html([run])
    assert html.startswith("<!doctype html>") and "__DATA__" not in html
    assert run["variants"][0]["text"] in html
