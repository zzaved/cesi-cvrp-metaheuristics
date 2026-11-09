"""Regression checks for the importable SA model and comparison helpers."""

import time

import numpy as np
import pytest

from cvrp import sa_vrptw as sa


@pytest.fixture(scope="session", autouse=True)
def compiled_setup():
    from cvrp.sa_static import warmup

    warmup()


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


def test_distance_mode_uses_exact_static_distances():
    problem = sa.make_problem(raw_instance(), mode="distance", distance_convention="exact")
    assert problem.distance[0, 1] == pytest.approx(np.sqrt(2))
    distance, schedule = sa.evaluate_route(problem, [1, 2])
    assert distance == schedule["distance"]
    assert schedule["departure"] == 0
    truncated = sa.make_problem(raw_instance(), mode="distance", distance_convention="truncated")
    assert truncated.distance[0, 1] == 1.4
    assert sa.make_problem(raw_instance()).distance[0, 1] == 1.4
    assert sa.make_problem(raw_instance(), mode="traffic").distance[0, 1] == pytest.approx(
        np.sqrt(2)
    )


def test_deadline_stops_inside_repair():
    problem = sa.make_problem(raw_instance())
    with pytest.raises(TimeoutError):
        sa.repair(problem, [], [1, 2], np.random.default_rng(0), deadline=time.perf_counter() - 1)


def test_distance_improvement_can_use_more_vehicles(monkeypatch):
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
    monkeypatch.setattr(sa, "repair", lambda *args, **kwargs: [[1, 2], [3]])
    for mode, expected_vehicles, expected_distance in (("benchmark", 1, 26), ("distance", 2, 24)):
        problem = sa.make_problem(raw, mode=mode)
        result = sa.anneal(problem, seed=0, initial=[[1, 3, 2]], alpha=0.1, min_temperature=0.5)
        assert result["iterations"] == 1
        assert result["metrics"]["vehicles"] == expected_vehicles
        assert result["metrics"]["distance"] == expected_distance


def test_time_budget_returns_feasible_best_and_reports_elapsed():
    problem = sa.make_problem(raw_instance(), mode="distance", distance_convention="exact")
    result = sa.anneal(problem, initial=[[1, 2]], alpha=0.999999999, time_limit=0.02)
    assert result["stop_reason"] == "time_limit"
    assert 0.02 <= result["elapsed"] < 0.5
    assert result["metrics"]["distance"] == pytest.approx(2 + 2 * np.sqrt(2))
    sa.validate(problem, result["routes"])
    with pytest.raises(ValueError):
        sa.anneal(problem, time_limit=0)


def test_infeasible_exact_reference_does_not_produce_a_gap(monkeypatch):
    raw = raw_instance()
    raw["time_window"][1] = [0, 2]
    problem = sa.make_problem(raw, mode="distance", distance_convention="exact")
    anneal = sa.anneal
    monkeypatch.setattr(
        sa,
        "anneal",
        lambda p, **kwargs: anneal(p, initial=[[1, 2]], alpha=0.1, min_temperature=0.5),
    )
    with pytest.raises(AssertionError, match="Time window/depot violation"):
        sa.run_experiment(problem, [[2, 1]], seeds=[0])


@pytest.mark.parametrize("mode", ["distance", "benchmark"])
def test_compiled_search_preserves_feasibility_and_improves_distance(mode):
    raw = dict(
        name="tradeoff",
        node_coord=[[0, 0], [1, 0], [2, 0], [-10, 0]],
        demand=[0, 1, 1, 1],
        time_window=[[0, 100]] * 4,
        service_time=[0] * 4,
        capacity=3,
        vehicles=3,
    )
    problem = sa.make_problem(raw, mode=mode)
    result = sa.anneal(problem, initial=[[1, 3, 2]], time_limit=0.05, accelerated=True)
    assert result["metrics"]["distance"] == 24
    if mode == "benchmark":
        assert result["metrics"]["vehicles"] == 1
    assert result["elapsed"] < 0.5
    assert result["stop_reason"] == "time_limit"
    sa.validate(problem, result["routes"])


def test_compiled_cost_matches_independent_validation():
    from cvrp.sa_static import _cost

    raw = raw_instance()
    raw["time_window"][1] = [0, 2]
    problem = sa.make_problem(raw, mode="distance", distance_convention="exact")
    for route in ([1, 2], [2, 1], [1], []):
        expected, _ = sa.evaluate_route(problem, route)
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


def test_measured_gap_is_preserved(monkeypatch):
    problem = sa.make_problem(raw_instance(), mode="distance", distance_convention="exact")
    metrics = sa.validate(problem, [[1], [2]])
    monkeypatch.setattr(
        sa,
        "anneal",
        lambda *args, **kwargs: dict(
            metrics=metrics,
            initial=metrics,
            elapsed=0.01,
            stop_reason="time_limit",
            iterations=1,
        ),
    )
    table, _ = sa.run_experiment(problem, [[1, 2]], seeds=[0])
    expected = 100 * (metrics["distance"] / (2 + 2 * np.sqrt(2)) - 1)
    assert expected > 0
    assert table.loc[0, "gap_pct"] == pytest.approx(expected)


def test_summary_uses_sample_standard_deviation():
    import pandas as pd

    rows = pd.DataFrame(
        dict(
            instance=["tiny"] * 2,
            algorithm=["sa"] * 2,
            seed=[0, 1],
            distance=[100.0, 120.0],
            gap_pct=[0.0, 20.0],
            elapsed_s=[1.0, 3.0],
            iterations=[10, 30],
        )
    )
    summary = sa.summarize_runs(rows).iloc[0]
    assert summary.runs == 2
    assert summary.distance_mean == 110
    assert summary.distance_std == pytest.approx(np.sqrt(200))
    assert summary.gap_mean == 10
    assert summary.gap_std == pytest.approx(np.sqrt(200))
    assert summary.iterations_std == pytest.approx(np.sqrt(200))


def test_local_solomon_loader_and_matched_ten_seed_runs(tmp_path):
    (tmp_path / "TINY.txt").write_text(
        "TINY\n\nVEHICLE\nNUMBER CAPACITY\n2 2\n\nCUSTOMER\n"
        "CUST NO. XCOORD. YCOORD. DEMAND READY TIME DUE DATE SERVICE TIME\n\n"
        "0 0 0 0 0 100 0\n1 1 1 1 0 100 0\n2 2 0 1 0 100 0\n"
    )
    (tmp_path / "TINY.sol").write_text("Route #1: 1 2\nCost: 4.8\n")
    problem, routes = sa.load_solomon(tmp_path, "TINY")
    assert problem.mode == "distance"
    assert problem.distance_convention == "truncated"
    assert sa.validate(problem, routes)["distance"] == pytest.approx(4.8)
    rows = sa.run_comparison(tmp_path, names=["TINY"], time_limit=0.01, algorithms=("sa", "tabu"))
    assert len(rows) == 20
    assert rows.groupby("algorithm").seed.nunique().eq(10).all()
    assert rows.feasible.all() and rows.reference_feasible.all()
    assert rows.gap_pct.notna().all()
    assert rows.iterations.gt(0).all()
    tabu = rows[rows.algorithm == "tabu"]
    assert tabu.iteration_unit.eq("outer_iterations").all()
    assert tabu.candidate_attempts.eq(tabu.iterations * 200).all()
    compiled = rows[rows.algorithm == "sa"]
    assert compiled.iteration_unit.eq("proposed_move_attempts").all()
    assert compiled.candidate_attempts.eq(compiled.iterations).all()
    default_rows = sa.run_comparison(tmp_path, time_limit=0.01)
    assert len(default_rows) == 10
    assert default_rows.algorithm.eq("sa").all()


def test_discovery_includes_all_56_pairs_and_requires_references(tmp_path):
    for i in range(56):
        (tmp_path / f"instance{i}.txt").touch()
        (tmp_path / f"instance{i}.sol").touch()
    names = sa.solomon_names(tmp_path)
    assert len(names) == 56
    assert set(names) == {f"instance{i}" for i in range(56)}
    (tmp_path / "unpaired.txt").touch()
    with pytest.raises(FileNotFoundError, match="unpaired.sol"):
        sa.solomon_names(tmp_path)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"initial_temperature_factor": 0},
        {"final_temperature": -1},
        {"initial_temperature_factor": float("nan")},
    ],
)
def test_invalid_temperature_settings_rejected(kwargs):
    from cvrp.sa_static import anneal_static

    problem = sa.make_problem(raw_instance())
    with pytest.raises(ValueError):
        anneal_static(problem, sa.initialize, sa.validate, **kwargs)
