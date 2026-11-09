"""Tests of the GRASP (src/cvrp/grasp.py)."""

import random
from pathlib import Path

import numpy as np
import pytest

from cvrp import Instance
from cvrp import grasp as gr
from cvrp.grasp import GRASPParams, grasp
from cvrp.utils import distance_matrix

DATA = Path(__file__).resolve().parents[1] / "data" / "solomon"


def _random_tw_instance(n: int = 40, seed: int = 3) -> Instance:
    """Random CVRPTW with tight windows built around a feasible schedule."""
    rng = np.random.default_rng(seed)
    coords = np.vstack([[50.0, 50.0], rng.uniform(0, 100, size=(n, 2))])
    demands = np.concatenate([[0.0], rng.integers(1, 10, size=n).astype(float)])
    d = distance_matrix(coords)
    centers = d[0] + rng.uniform(0, 300, size=n + 1)
    ready = np.maximum(0.0, centers - 15)
    due = centers + 15
    ready[0], due[0] = 0.0, 1000.0
    service = np.full(n + 1, 5.0)
    service[0] = 0.0
    return Instance(
        name="rand-tw",
        coords=coords,
        demands=demands,
        capacity=60,
        num_vehicles=n,
        ready_times=ready,
        due_times=due,
        service_times=service,
    )


def test_grasp_feasible_on_tiny(tiny: Instance):
    res = grasp(tiny, GRASPParams(iterations=5), seed=0)
    assert res.best.is_feasible(tiny)
    assert res.cost == pytest.approx(res.best.cost(tiny))


def test_grasp_feasible_with_time_windows(tiny_tw: Instance):
    res = grasp(tiny_tw, GRASPParams(iterations=5, perturb_kicks=3), seed=0)
    assert res.best.is_feasible(tiny_tw)


def test_grasp_is_reproducible():
    inst = Instance.random(50, seed=5)
    a = grasp(inst, GRASPParams(iterations=5), seed=7)
    b = grasp(inst, GRASPParams(iterations=5), seed=7)
    assert a.cost == b.cost
    assert a.best.routes == b.best.routes


@pytest.mark.parametrize("improvement", ["first", "best"])
def test_fast_checks_agree_with_shared_evaluator(improvement: str):
    """The O(1) caches must never accept a move the shared evaluator rejects."""
    inst = _random_tw_instance()
    params = GRASPParams(improvement=improvement)
    m = gr._Model(inst, params.n_neighbors)
    rng = random.Random(1)
    for _ in range(5):
        st = gr.construct(m, rng, 0.3, "regret", 0.0)
        assert st.to_solution().is_feasible(inst)
        built = st.cost()
        gr._LocalSearch(m, st, rng, params).run()
        sol = st.to_solution()
        assert sol.violations(inst) == []
        assert st.cost() <= built + 1e-9
        assert st.cost() == pytest.approx(sol.cost(inst))


def test_local_search_never_worsens():
    inst = Instance.random(80, seed=2, distribution="clustered")
    m = gr._Model(inst, 20)
    rng = random.Random(0)
    st = gr.construct(m, rng, 0.5, "cheapest", 0.0)
    before = st.cost()
    gr._LocalSearch(m, st, rng, GRASPParams()).run()
    assert st.cost() <= before + 1e-9


@pytest.mark.skipif(not (DATA / "C101.txt").exists(), reason="Solomon C101 not downloaded")
def test_solomon_c101_reaches_reference():
    inst = Instance.from_vrplib(DATA / "C101.txt", instance_format="solomon")
    inst.dist = distance_matrix(inst.coords, "floor1")
    res = grasp(inst, GRASPParams(iterations=10), seed=1)
    assert res.best.is_feasible(inst)
    assert res.cost <= 827.3 * 1.01


# ---------------------------------------------------------------- traffic mode
def _working_day(n: int = 40, seed: int = 3) -> Instance:
    """Random customers with windows inside a 08:00-18:00 working day (minutes)."""
    base = Instance.random(n, capacity=100, seed=seed)
    rng = np.random.default_rng(seed)
    ready = np.concatenate([[480.0], rng.uniform(480, 900, n)])
    due = np.concatenate([[1080.0], ready[1:] + rng.uniform(60, 180, n)])
    service = np.concatenate([[0.0], np.full(n, 10.0)])
    return Instance(
        name=f"day-n{n}",
        coords=base.coords,
        demands=base.demands,
        capacity=100,
        num_vehicles=12,
        ready_times=ready,
        due_times=due,
        service_times=service,
    )


def test_traffic_cost_is_the_tabu_duration():
    from cvrp.tabu import duration_cost

    inst = _working_day()
    res = grasp(inst, GRASPParams(iterations=3, objective="duration"), seed=0)
    cost = duration_cost(inst, start_min=480.0)
    assert res.best is not None and res.best.is_feasible(inst)
    assert len(res.best.routes) <= inst.num_vehicles
    assert res.cost == pytest.approx(sum(cost(tuple(r)) for r in res.best.routes))


def test_traffic_mode_is_reproducible():
    inst = _working_day()
    p = GRASPParams(iterations=2, objective="duration")
    assert grasp(inst, p, seed=5).cost == grasp(inst, p, seed=5).cost


def test_unknown_objective_is_rejected():
    with pytest.raises(ValueError):
        grasp(Instance.random(10, seed=0), GRASPParams(objective="speed"))
