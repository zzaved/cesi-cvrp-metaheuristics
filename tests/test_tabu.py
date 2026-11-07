import math

import pytest

from cvrp import Instance
from cvrp.tabu import TabuParams, distance_cost, duration_cost, nearest_feasible, tabu_search

TINY_OPTIMUM = 10 + 2**0.5  # same value as tests/test_ilp.py


def _served_once(routes, inst: Instance) -> bool:
    return sorted(c for r in routes for c in r) == list(range(1, inst.n_customers + 1))


def test_reaches_tiny_optimum(tiny: Instance):
    res = tabu_search(tiny, distance_cost(tiny), TabuParams(time_limit=0.5), seed=1)
    assert _served_once(res.routes, tiny)
    assert res.cost == pytest.approx(TINY_OPTIMUM)


def test_costs_reject_infeasible_routes(tiny: Instance, tiny_tw: Instance):
    assert math.isinf(distance_cost(tiny)((1, 2, 5)))  # load 13 > Q = 10
    assert math.isfinite(duration_cost(tiny_tw, start_min=0.0)((1, 2)))
    assert _served_once(nearest_feasible(tiny_tw, distance_cost(tiny_tw)), tiny_tw)
