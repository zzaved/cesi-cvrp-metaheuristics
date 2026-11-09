"""Public SA solver contract, shared with the GRASP-style repository API."""

import math

import numpy as np
import pytest

from cvrp.sa import SAParams, SAResult, sa, simulated_annealing
from cvrp.sa_static import warmup
from cvrp.solution import Solution


@pytest.fixture(scope="module", autouse=True)
def compiled_setup():
    warmup()


@pytest.mark.parametrize("fixture", ["tiny", "tiny_tw"])
def test_shared_result_contract_and_input_immutability(request, fixture):
    inst = request.getfixturevalue(fixture)
    before = inst.dist.copy(), inst.demands.copy(), inst.coords.copy()
    result = sa(inst, SAParams(time_limit=0.02), seed=1)
    assert isinstance(result, SAResult)
    assert isinstance(result.best, Solution)
    assert result.best.violations(inst) == []
    assert result.cost == pytest.approx(result.best.cost(inst))
    assert result.iterations > 0 and result.runtime >= 0.02
    assert result.initial.is_feasible(inst)
    assert result.cost <= result.initial.cost(inst) + 1e-8
    assert result.history[-1]["best"] == pytest.approx(result.cost)
    assert all("iteration" in r and "seconds" in r for r in result.history)
    assert all(
        a["best"] >= b["best"] - 1e-8
        for a, b in zip(result.history, result.history[1:], strict=False)
    )
    for current, old in zip((inst.dist, inst.demands, inst.coords), before, strict=True):
        np.testing.assert_array_equal(current, old)


def test_iteration_cap_honors_partial_batch_and_copies_initial(tiny):
    initial = Solution([[1, 2], [3, 4], [5, 6]])
    routes = [r[:] for r in initial.routes]
    result = simulated_annealing(
        tiny,
        SAParams(iterations=257, time_limit=1),
        seed=None,
        initial=initial,
    )
    assert result.iterations == 257
    assert result.stop_reason == "iterations"
    assert initial.routes == routes
    assert result.best.is_feasible(tiny)
    assert all(r["iteration"] <= 257 for r in result.history)


def test_cost_uses_the_supplied_matrix(tiny):
    tiny.dist *= 1.25
    result = sa(tiny, SAParams(iterations=256, time_limit=1), seed=1)
    assert result.cost == pytest.approx(result.best.cost(tiny))


def test_invalid_initial_solution_is_rejected(tiny):
    with pytest.raises(ValueError, match="Infeasible initial"):
        sa(tiny, initial=Solution([[1, 2]]))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"time_limit": 0},
        {"iterations": 0},
        {"iterations": 1.5},
        {"initial_temperature_factor": -1},
        {"final_temperature": math.inf},
    ],
)
def test_invalid_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        SAParams(**kwargs)
