import numpy as np
import pytest

from cvrp import Instance
from cvrp.ilp import solve_cvrp_flow, solve_cvrp_mtz, solve_cvrp_rcc, solve_cvrptw, solve_tdvrptw
from cvrp.tabu import RHO

# Optimum of the tiny instance, found by hand: 4 + 4 + 2 + sqrt(2).
TINY_OPTIMUM = 10 + 2**0.5
FORMULATIONS = [solve_cvrp_mtz, solve_cvrp_flow, solve_cvrp_rcc]


@pytest.mark.parametrize("solve", FORMULATIONS)
def test_formulations_find_the_optimum(tiny: Instance, solve):
    res = solve(tiny, time_limit=10)
    assert res.status == "Optimal"
    assert res.objective == pytest.approx(TINY_OPTIMUM, abs=1e-6)
    assert res.solution.is_feasible(tiny)
    assert res.solution.cost(tiny) == pytest.approx(res.objective, abs=1e-6)


@pytest.mark.parametrize("solve", FORMULATIONS)
def test_lp_relaxation_is_a_lower_bound(tiny: Instance, solve):
    res = solve(tiny, time_limit=10, relax=True)
    assert res.status == "LP"
    assert res.lower_bound <= TINY_OPTIMUM + 1e-6


def test_cvrptw_respects_windows(tiny_tw: Instance):
    tiny_tw.ready_times[1] = 5.0  # customer 1 opens late: waiting is allowed
    tiny_tw.due_times[1] = 6.0
    res = solve_cvrptw(tiny_tw, time_limit=10)
    assert res.status == "Optimal"
    assert res.solution.is_feasible(tiny_tw)
    assert res.objective >= TINY_OPTIMUM - 1e-6


def test_cvrptw_needs_windows(tiny: Instance):
    with pytest.raises(ValueError):
        solve_cvrptw(tiny)


def toy_notebook_01() -> Instance:
    """The toy instance of notebook 01 (times in minutes after midnight, c_ij in minutes)."""
    coords = np.array([[0, 0], [1, 0], [2, 0], [0, 1], [0, 2], [-1, 0], [0, -1]], dtype=float)
    return Instance(
        name="toy",
        coords=coords,
        demands=np.array([0, 4, 4, 3, 3, 5, 5]),
        capacity=10,
        num_vehicles=3,
        ready_times=np.array([360, 480, 480, 420, 540, 600, 600], dtype=float),
        due_times=np.array([1200, 540, 660, 480, 600, 840, 840], dtype=float),
        service_times=np.array([0, 10, 10, 10, 10, 10, 10], dtype=float),
        dist=10 * np.linalg.norm(coords[:, None] - coords[None], axis=2),
    )


def test_traffic_model_finds_the_toy_optimum():
    # 247.16 min: optimum found by enumerating every partition, order and departure time
    # (0.25 min grid); the hand solution of notebook 01 takes 256.5 min.
    res = solve_tdvrptw(toy_notebook_01(), RHO, time_limit=60)
    assert res.status == "Optimal"
    assert res.objective == pytest.approx(247.1604, abs=1e-3)
    assert sorted(sorted(r) for r in res.solution.routes) == [[1, 3], [2, 4], [5, 6]]


def test_traffic_relaxation_is_a_lower_bound():
    res = solve_tdvrptw(toy_notebook_01(), RHO, time_limit=60, relax=True)
    assert res.status == "LP"
    assert res.lower_bound <= 247.1604 + 1e-6


def test_traffic_model_needs_windows(tiny: Instance):
    with pytest.raises(ValueError):
        solve_tdvrptw(tiny, RHO)
