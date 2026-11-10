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


@pytest.mark.parametrize("fixture", ["tiny", "tiny_tw"])
def test_untimed_shared_solver_is_feasible_and_seed_reproducible(request, fixture):
    inst = request.getfixturevalue(fixture)
    initial = Solution([[1, 2], [3, 4], [5, 6]])
    before = initial.copy().routes
    params = SAParams(time_limit=None, iterations=1025)
    first = sa(inst, params, seed=7, initial=initial)
    second = sa(inst, params, seed=7, initial=initial)
    assert first.iterations == second.iterations == 1025
    assert first.stop_reason == second.stop_reason == "iterations"
    assert first.best.is_feasible(inst)
    assert second.best.routes == first.best.routes
    assert second.cost == first.cost <= initial.cost(inst) + 1e-8
    assert first.accepted == second.accepted
    assert initial.routes == before


def test_untimed_cooling_ignores_clock_and_reaches_final_temperature(tiny, monkeypatch):
    import itertools
    from types import SimpleNamespace

    from cvrp import sa_static
    from cvrp.sa_vrptw import problem_from_instance, validate

    clock = itertools.count(0, 1_000_000)
    monkeypatch.setattr(sa_static, "time", SimpleNamespace(perf_counter=lambda: next(clock)))
    temperatures = []
    original_batch = sa_static._batch

    def capture(*args):
        temperatures.append(args[12])
        return original_batch(*args)

    def initialize(problem, rng, deadline):
        assert deadline == math.inf
        return [[1, 2], [3, 4], [5, 6]]

    monkeypatch.setattr(sa_static, "_batch", capture)
    result = sa_static.anneal_static(
        problem_from_instance(tiny), initialize, validate,
        time_limit=None, max_iterations=257, final_temperature=0.02,
    )
    assert result["iterations"] == 257
    assert result["stop_reason"] == "iterations"
    assert result["time_limit"] is None
    assert len(temperatures) == 2
    assert temperatures[0] > temperatures[1]
    assert temperatures[-1] == pytest.approx(0.02)
    assert Solution(result["routes"]).is_feasible(tiny)


def test_untimed_engine_requires_a_finite_move_schedule(tiny):
    from cvrp.sa_static import anneal_static
    from cvrp.sa_vrptw import initialize, problem_from_instance, validate

    with pytest.raises(ValueError, match="max_iterations is required"):
        anneal_static(problem_from_instance(tiny), initialize, validate, time_limit=None)


def test_capacity_bounded_padding_preserves_the_sa_search(monkeypatch):
    from types import SimpleNamespace

    from cvrp import Instance, sa_static
    from cvrp.sa_vrptw import initialize, problem_from_instance, validate

    inst = Instance.random(n=100, seed=4)
    inst.capacity = 5
    inst.demands[1:] = 1
    initial = [list(range(start, start + 5)) for start in range(1, 101, 5)]
    problem = problem_from_instance(inst)
    kwargs = dict(time_limit=None, max_iterations=4097, initial=initial, seed=3)
    compact = sa_static.anneal_static(problem, initialize, validate, **kwargs)
    # Disable only the capacity-based allocation shortcut to compare the exact
    # proposed-move sequence with full n+1 padding under the same seed.
    full_numpy = SimpleNamespace(**(vars(np) | {"all": lambda values: False}))
    monkeypatch.setattr(sa_static, "np", full_numpy)
    full = sa_static.anneal_static(problem, initialize, validate, **kwargs)
    assert compact["routes"] == full["routes"]
    assert compact["metrics"]["distance"] == full["metrics"]["distance"]
    assert compact["accepted"] == full["accepted"]
