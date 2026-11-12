"""SA-only tuning and full-dataset benchmark validation."""

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from cvrp.sa_protocol import (
    benchmark_jobs,
    choose_parameters,
    tuning_jobs,
    validate_runs,
)


def fake_study():
    tuning = ["C101", "C201", "R101", "R201", "RC101", "RC201"]
    test = [f"TEST{i}" for i in range(50)]
    grid = [
        {"initial_temperature_factor": factor, "final_temperature": final}
        for factor in (0.0025, 0.005, 0.01)
        for final in (0.005, 0.01, 0.02, 0.05)
    ]
    return SimpleNamespace(
        DATA=SimpleNamespace(glob=lambda _: [Path(n + ".txt") for n in tuning + test]),
        TUNING=tuning,
        TUNE_SEEDS=[101, 102],
        TEST_SEEDS=list(range(1, 11)),
        TIME_LIMIT=20.0,
        tune_jobs=lambda _: [(n, "sa", p, s) for n in tuning for p in grid for s in (101, 102)],
    )


def test_six_tuning_and_fifty_test_instances():
    study = fake_study()
    tuning = tuning_jobs(study)
    test = benchmark_jobs(study, {"final_temperature": 0.02})
    assert len(tuning) == 144 and len(test) == 500
    assert {s for _, _, _, s in tuning} == {101, 102}
    assert {s for _, _, _, s in test} == set(range(1, 11))
    tune_names = {n for n, _, _, _ in tuning}
    test_names = {n for n, _, _, _ in test}
    assert len(tune_names) == 6 and len(test_names) == 50
    assert tune_names.isdisjoint(test_names)
    assert len(tune_names | test_names) == 56
    assert {a for _, a, _, _ in test} == {"sa"}
    assert all(p["time_limit"] == 20 for _, _, p, _ in tuning + test)
    assert len(tuning_jobs(study, quick_check=True)) == 72
    assert len(benchmark_jobs(study, {}, quick_check=True)) == 100


def test_parameter_selection_uses_only_supplied_tuning_gaps():
    rows = pd.DataFrame(
        dict(
            params=["{'final_temperature': 0.01, 'time_limit': 20}"] * 2
            + ["{'final_temperature': 0.02, 'time_limit': 20}"] * 2,
            gap=[0, 4, 1, 2],
            feasible=[True] * 4,
        )
    )
    chosen, ranking = choose_parameters(rows)
    assert chosen == {"final_temperature": 0.02}
    assert ranking.iloc[0].mean_gap == 1.5


def campaign(algorithm="sa", delta=0):
    return pd.DataFrame(
        [
            dict(
                instance=n,
                algorithm=algorithm,
                seed=s,
                cost=100 + delta,
                best_known=100,
                gap=delta,
                seconds=20.01,
                iterations=256,
                routes=3,
                feasible=True,
                params="{}",
            )
            for n in ("A", "B")
            for s in (1, 2)
        ]
    )


@pytest.mark.parametrize("problem", ["missing", "duplicate", "quick", "infeasible", "gap"])
def test_invalid_benchmark_records_are_rejected(problem):
    rows = campaign()
    if problem == "missing":
        rows = rows.iloc[:-1]
    elif problem == "duplicate":
        rows = pd.concat([rows, rows.iloc[:1]])
    elif problem == "quick":
        rows.loc[0, "seconds"] = 1
    elif problem == "infeasible":
        rows.loc[0, "feasible"] = False
    else:
        rows.loc[0, "gap"] = 10
    with pytest.raises(ValueError):
        validate_runs(rows, ["A", "B"], [1, 2])


def test_single_seed_untimed_jobs_keep_tuning_and_test_separate():
    study = fake_study()
    budget = dict(seeds=(1,), time_limit=None, iterations=10_000_000)
    tuning = tuning_jobs(study, **budget)
    test = benchmark_jobs(study, {"final_temperature": 0.02}, **budget)
    assert len(tuning) == 72 and len(test) == 50
    assert {s for _, _, _, s in tuning + test} == {1}
    assert {n for n, _, _, _ in tuning}.isdisjoint({n for n, _, _, _ in test})
    assert all(p["time_limit"] is None for _, _, p, _ in tuning + test)
    assert all(p["iterations"] == 10_000_000 for _, _, p, _ in tuning + test)


def test_untimed_selection_returns_only_temperature_settings():
    rows = pd.DataFrame([dict(
        params="{'final_temperature': 0.02, 'time_limit': None, 'iterations': 1000}",
        gap=1.0, feasible=True,
    )])
    chosen, _ = choose_parameters(rows)
    assert chosen == {"final_temperature": 0.02}


def test_untimed_validation_uses_completed_moves_instead_of_elapsed_time():
    rows = campaign()
    rows["seconds"] = 0.001
    rows["params"] = "{'time_limit': None, 'iterations': 256}"
    validate_runs(rows, ["A", "B"], [1, 2], time_limit=None, iterations=256)
    with pytest.raises(ValueError, match="positive iteration budget"):
        validate_runs(rows, ["A", "B"], [1, 2], time_limit=None)
    rows.loc[0, "iterations"] = 255
    with pytest.raises(ValueError, match="iteration budget"):
        validate_runs(rows, ["A", "B"], [1, 2], time_limit=None, iterations=256)
    rows.loc[0, "iterations"] = 256
    rows.loc[0, "params"] = "{'time_limit': 20, 'iterations': 256}"
    with pytest.raises(ValueError, match="disabled time limit"):
        validate_runs(rows, ["A", "B"], [1, 2], time_limit=None, iterations=256)
