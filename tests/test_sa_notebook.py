"""Regression checks for the standalone SA notebook's comparison modes."""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sa(tmp_path):
    pytest.importorskip("numba")
    notebook = Path(__file__).resolve().parents[1] / "notebooks" / "SA.ipynb"
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    namespace = {"ROOT": tmp_path, "pd": pd}
    for index in (6, 9, 11):
        exec(compile("".join(cells[index]["source"]), str(notebook), "exec"), namespace)
    helpers = "".join(cells[16]["source"]).split("SEEDS =")[0]
    exec(compile(helpers, str(notebook), "exec"), namespace)
    return namespace


def raw_instance():
    return dict(
        name="tiny",
        node_coord=[[0, 0], [1, 1], [2, 0]],
        demand=[0, 1, 1],
        time_window=[[0, 100]] * 3,
        service_time=[0, 0, 0],
        capacity=2,
        vehicles=2,
    )


def test_distance_mode_uses_exact_static_distances(sa):
    problem = sa["make_problem"](raw_instance(), mode="distance")
    assert problem.distance[0, 1] == pytest.approx(np.sqrt(2))
    distance, schedule = sa["evaluate_route"](problem, [1, 2])
    assert distance == schedule["distance"]
    assert schedule["departure"] == 0
    truncated = sa["make_problem"](
        raw_instance(), mode="distance", distance_convention="truncated"
    )
    assert truncated.distance[0, 1] == 1.4
    assert sa["make_problem"](raw_instance()).distance[0, 1] == 1.4


def test_deadline_stops_inside_repair(sa):
    problem = sa["make_problem"](raw_instance())
    with pytest.raises(TimeoutError):
        sa["repair"](
            problem, [], [1, 2], np.random.default_rng(0), deadline=time.perf_counter() - 1
        )


def test_distance_improvement_can_use_more_vehicles(sa):
    raw = dict(
        name="tradeoff",
        node_coord=[[0, 0], [1, 0], [2, 0], [-10, 0]],
        demand=[0, 1, 1, 1],
        time_window=[[0, 100]] * 4,
        service_time=[0] * 4,
        capacity=3,
        vehicles=3,
    )
    # Present exactly one move: 26 distance / 1 vehicle -> 24 distance / 2 vehicles.
    sa["repair"] = lambda *args, **kwargs: [[1, 2], [3]]
    for mode, expected_vehicles, expected_distance in (("benchmark", 1, 26), ("distance", 2, 24)):
        problem = sa["make_problem"](raw, mode=mode)
        result = sa["anneal"](problem, seed=0, initial=[[1, 3, 2]], alpha=0.1, min_temperature=0.5)
        assert result["iterations"] == 1
        assert result["metrics"]["vehicles"] == expected_vehicles
        assert result["metrics"]["distance"] == expected_distance


def test_time_budget_returns_feasible_best_and_reports_elapsed(sa):
    problem = sa["make_problem"](raw_instance(), mode="distance")
    result = sa["anneal"](problem, initial=[[1, 2]], alpha=0.999999999, time_limit=0.02)
    assert result["stop_reason"] == "time_limit"
    assert 0.02 <= result["elapsed"] < 0.5
    assert result["metrics"]["distance"] == pytest.approx(2 + 2 * np.sqrt(2))
    sa["validate"](problem, result["routes"])
    with pytest.raises(ValueError):
        sa["anneal"](problem, time_limit=0)


def test_infeasible_exact_reference_does_not_produce_a_gap(sa):
    raw = raw_instance()
    raw["time_window"][1] = [0, 2]
    problem = sa["make_problem"](raw, mode="distance")
    anneal = sa["anneal"]
    sa["anneal"] = lambda p, **kwargs: anneal(p, initial=[[1, 2]], alpha=0.1, min_temperature=0.5)
    table, _ = sa["run_experiment"](problem, [[2, 1]], seeds=[0])
    assert not table.loc[0, "reference_feasible"]
    assert np.isnan(table.loc[0, "gap_pct"])
    assert table.loc[0, "feasible"]
    assert table.loc[0, "algorithm"] == "sa_distance_exact"


@pytest.mark.parametrize("mode", ["distance", "benchmark"])
def test_compiled_search_preserves_feasibility_and_improves_distance(sa, mode):
    raw = dict(
        name="tradeoff",
        node_coord=[[0, 0], [1, 0], [2, 0], [-10, 0]],
        demand=[0, 1, 1, 1],
        time_window=[[0, 100]] * 4,
        service_time=[0] * 4,
        capacity=3,
        vehicles=3,
    )
    problem = sa["make_problem"](raw, mode=mode)
    result = sa["anneal"](problem, initial=[[1, 3, 2]], time_limit=0.05, accelerated=True)
    assert result["metrics"]["distance"] == 24
    if mode == "benchmark":
        assert result["metrics"]["vehicles"] == 1
    assert result["elapsed"] < 0.5
    assert result["stop_reason"] == "time_limit"
    sa["validate"](problem, result["routes"])


def test_compiled_cost_matches_independent_validation(sa):
    from cvrp.sa_static import _cost

    raw = raw_instance()
    raw["time_window"][1] = [0, 2]
    problem = sa["make_problem"](raw, mode="distance")
    for route in ([1, 2], [2, 1], [1], []):
        expected, _ = sa["evaluate_route"](problem, route)
        padded = np.zeros(problem.n + 1, dtype=np.int64)
        padded[: len(route)] = route
        actual = _cost(
            padded,
            len(route),
            problem.distance,
            problem.q,
            problem.tw,
            problem.service,
            problem.capacity,
        )
        assert actual == pytest.approx(expected)


def test_measured_gap_is_preserved(sa):
    problem = sa["make_problem"](raw_instance(), mode="distance")
    metrics = sa["validate"](problem, [[1], [2]])
    sa["anneal"] = lambda *args, **kwargs: dict(
        metrics=metrics,
        initial=metrics,
        elapsed=0.01,
        stop_reason="time_limit",
        iterations=1,
    )
    table, _ = sa["run_experiment"](problem, [[1, 2]], seeds=[0])
    expected = 100 * (metrics["distance"] / (2 + 2 * np.sqrt(2)) - 1)
    assert expected > 0
    assert table.loc[0, "gap_pct"] == pytest.approx(expected)
