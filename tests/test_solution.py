import pytest

from cvrp import Instance, Solution
from cvrp.solution import route_cost
from cvrp.timewindows import is_route_tw_feasible, route_schedule


def test_route_cost(tiny: Instance):
    # 0 -> 1 -> 2 -> 0 on the x axis: 1 + 1 + 2
    assert route_cost([1, 2], tiny.dist) == pytest.approx(4.0)
    assert route_cost([], tiny.dist) == 0.0


def test_feasible_solution(tiny: Instance):
    sol = Solution([[1, 2], [3, 4], [5, 6]])
    assert sol.is_feasible(tiny)
    assert sol.cost(tiny) == pytest.approx(4 + 4 + 2 + 2**0.5)


def test_violations_are_reported(tiny: Instance):
    problems = Solution([[1, 2, 3], [3, 4]]).violations(tiny)
    text = " ".join(problems)
    assert "not visited" in text
    assert "more than once" in text
    assert "over capacity" in text


def test_waiting_is_allowed(tiny_tw: Instance):
    tiny_tw.ready_times[1] = 5.0
    sched = route_schedule([1], tiny_tw)
    assert sched["wait"][1] == pytest.approx(4.0)
    assert is_route_tw_feasible([1], tiny_tw)


def test_late_arrival_is_infeasible(tiny_tw: Instance):
    tiny_tw.due_times[2] = 1.0
    assert not is_route_tw_feasible([1, 2], tiny_tw)
