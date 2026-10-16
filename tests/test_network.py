import numpy as np

from jevsim.simulator import build_network, sample_label
from jevsim.simulator.network import highest_degree_node


def test_network_shape_and_seed():
    g = build_network(seed=1)
    assert g.number_of_nodes() == 64
    assert sum(1 for *_, d in g.edges(data=True) if d["kind"] == "long") == 5
    assert all(g.degree[v] >= 3 for v in g)
    assert sorted(build_network(seed=1).edges) == sorted(g.edges)
    assert sorted(build_network(seed=2).edges) != sorted(g.edges)
    assert highest_degree_node(g) == highest_degree_node(build_network(seed=1))


def test_sampling_is_seeded():
    probs = {"true": 0.3, "false": 0.7}
    a = [sample_label(probs, np.random.default_rng(5)) for _ in range(3)]
    b = [sample_label(probs, np.random.default_rng(5)) for _ in range(3)]
    assert a == b
    rng = np.random.default_rng(0)
    draws = [sample_label(probs, rng) for _ in range(4000)]
    assert abs(draws.count("true") / 4000 - 0.3) < 0.03
