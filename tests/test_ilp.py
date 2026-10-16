import pytest

from cvrp import Instance
from cvrp.ilp import solve_cvrp_flow, solve_cvrp_mtz, solve_cvrp_rcc, solve_cvrptw

# Optimum of the tiny instance, checked by brute force in notebook 01: 4 + 4 + 2 + sqrt(2).
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
