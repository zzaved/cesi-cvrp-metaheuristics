"""End to end smoke test: instance -> construction -> ALNS -> local search -> checks."""

from cvrp import Instance
from cvrp.alns import ALNSParams, alns
from cvrp.construct import nearest_neighbor
from cvrp.neighborhoods import local_search
from cvrp.utils import gap_percent


def test_full_pipeline_on_tiny(tiny: Instance):
    start = nearest_neighbor(tiny)
    res = alns(tiny, ALNSParams(iterations=200), seed=0, initial=start)
    best = local_search(res.best, tiny)
    assert best.is_feasible(tiny)
    assert best.cost(tiny) <= start.cost(tiny) + 1e-9
    assert len(res.best_history) == res.iterations


def test_alns_is_reproducible_and_improves():
    inst = Instance.random(40, seed=7)
    a = alns(inst, ALNSParams(iterations=300), seed=42)
    b = alns(inst, ALNSParams(iterations=300), seed=42)
    assert a.best_cost == b.best_cost
    nn_cost = nearest_neighbor(inst).cost(inst)
    assert a.best_cost <= nn_cost
    assert gap_percent(a.best_cost, nn_cost) <= 0


def test_alns_with_time_windows(tiny_tw: Instance):
    res = alns(tiny_tw, ALNSParams(iterations=100), seed=0)
    assert res.best.is_feasible(tiny_tw)
