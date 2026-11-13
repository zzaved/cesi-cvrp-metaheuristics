"""GRASP descent on an asymmetric matrix (one-way streets): every applied move must improve."""

import random

import numpy as np

from cvrp import grasp as g
from cvrp.instance import Instance


def _asymmetric(n: int = 40, seed: int = 3) -> Instance:
    rng = np.random.default_rng(seed)
    xy = rng.uniform(0, 100, size=(n + 1, 2))
    base = np.linalg.norm(xy[:, None] - xy[None, :], axis=2)
    dist = base * rng.uniform(1.0, 1.6, size=base.shape)  # d[i, j] != d[j, i]
    np.fill_diagonal(dist, 0.0)
    return Instance(
        name="asym",
        coords=xy,
        demands=np.concatenate([[0.0], rng.integers(1, 6, size=n).astype(float)]),
        capacity=40.0,
        dist=dist,
    )


def test_descent_never_worsens_on_asymmetric_matrix():
    inst = _asymmetric()
    m = g._Model(inst, 10)
    rng = random.Random(0)
    st = g.construct(m, rng, 0.3, "regret", 0.0)
    ls = g._LocalSearch(m, st, rng, g.GRASPParams())

    def true_cost() -> float:
        return sum(
            sum(m.D[a][b] for a, b in zip([0, *r.customers()], [*r.customers(), 0]))
            for r in st.routes
        )

    costs = [true_cost()]
    apply = ls._apply

    def tracked(mv):
        apply(mv)
        costs.append(true_cost())

    ls._apply = tracked
    moves = ls.run()
    assert moves < g.GRASPParams().max_local_rounds  # the descent stops by itself
    assert all(b <= a + 1e-9 for a, b in zip(costs, costs[1:]))
