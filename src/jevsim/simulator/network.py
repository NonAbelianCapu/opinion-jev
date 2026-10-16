"""The contact network: a jittered 8x8 grid, 3 nearest neighbors plus 5 random long links."""

import networkx as nx
import numpy as np


def build_network(seed: int, side: int = 8, k_nearest: int = 3, long_links: int = 5,
                  jitter: float = 0.3) -> nx.Graph:
    rng = np.random.default_rng(seed)
    n = side * side
    grid = np.array([(i % side, i // side) for i in range(n)], dtype=float)
    pos = grid + rng.uniform(-jitter, jitter, size=grid.shape)

    g = nx.Graph()
    for i in range(n):
        g.add_node(i, pos=tuple(pos[i]))
    dist = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=-1)
    for i in range(n):
        for j in np.argsort(dist[i])[1 : k_nearest + 1]:
            g.add_edge(i, int(j), kind="near")

    added = 0
    while added < long_links:
        a, b = (int(x) for x in rng.choice(n, size=2, replace=False))
        if not g.has_edge(a, b):
            g.add_edge(a, b, kind="long")
            added += 1
    return g


def highest_degree_node(g: nx.Graph) -> int:
    """Default seed node; ties go to the lowest id so the choice is reproducible."""
    return min(g.nodes, key=lambda v: (-g.degree[v], v))
