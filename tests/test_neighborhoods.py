from cvrp import Instance, Solution
from cvrp.construct import nearest_neighbor
from cvrp.neighborhoods import local_search, relocate, two_opt_route


def test_nearest_neighbor_is_feasible(tiny: Instance):
    assert nearest_neighbor(tiny).is_feasible(tiny)


def test_nearest_neighbor_on_random_instance():
    inst = Instance.random(80, seed=3)
    assert nearest_neighbor(inst).is_feasible(inst)


def test_two_opt_removes_a_crossing():
    inst = Instance.random(8, capacity=1000, seed=0)
    crossed = [1, 3, 2, 4, 5, 7, 6, 8]
    improved, _ = two_opt_route(crossed, inst)
    assert Solution([improved]).cost(inst) <= Solution([crossed]).cost(inst) + 1e-9
    assert sorted(improved) == sorted(crossed)


def test_relocate_improves_and_keeps_feasibility(tiny: Instance):
    sol = Solution([[1, 3], [2, 4], [5, 6]])
    before = sol.cost(tiny)
    assert relocate(sol, tiny)
    assert sol.cost(tiny) < before
    assert sol.is_feasible(tiny)


def test_local_search_never_worsens():
    inst = Instance.random(60, seed=5, distribution="clustered")
    sol = nearest_neighbor(inst)
    before = sol.cost(inst)
    local_search(sol, inst)
    assert sol.cost(inst) <= before + 1e-9
    assert sol.is_feasible(inst)
