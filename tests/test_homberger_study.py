"""Validate matched-seed Homberger comparisons across runtime budgets."""

import numpy as np
import pandas as pd
import pytest

from cvrp import Instance, Solution
from experiments.homberger_study import lower_bounds, validate_budget_runs

NAMES = ("R1_4_1", "R1_8_1", "R1_10_1")
SEEDS = (1, 2, 3)
BUDGETS = (20.0, 60.0, 120.0)


def campaign():
    return pd.DataFrame([
        dict(instance=name, seed=seed, time_limit=budget, params="{'factor': 0.01}",
             best_known=100.0, cost=110.0, gap=10.0, seconds=budget + 0.01,
             iterations=1000, feasible=True, stop_reason="time_limit")
        for name in NAMES for seed in SEEDS for budget in BUDGETS
    ])


def test_complete_matched_seed_budget_comparison():
    rows = campaign()
    validate_budget_runs(rows, NAMES, SEEDS, BUDGETS)
    assert len(rows) == 27


@pytest.mark.parametrize("problem", ["missing", "duplicate", "parameters", "gap", "short", "cap"])
def test_inconsistent_budget_comparisons_are_rejected(problem):
    rows = campaign()
    if problem == "missing":
        rows = rows.iloc[:-1]
    elif problem == "duplicate":
        rows = pd.concat([rows, rows.iloc[:1]])
    elif problem == "parameters":
        rows.loc[0, "params"] = "{'factor': 0.02}"
    elif problem == "gap":
        rows.loc[0, "gap"] = 9.0
    elif problem == "short":
        rows.loc[0, "seconds"] = 1.0
    else:
        rows.loc[0, "stop_reason"] = "iterations"
    with pytest.raises(ValueError):
        validate_budget_runs(rows, NAMES, SEEDS, BUDGETS)


def test_unsuccessful_runs_remain_visible_without_fabricated_gaps():
    rows = campaign()
    rows.loc[0, ["cost", "gap"]] = np.nan
    rows.loc[0, "feasible"] = False
    rows.loc[0, "stop_reason"] = "initialization_timeout"
    rows.loc[0, "iterations"] = 0
    validate_budget_runs(rows, NAMES, SEEDS, BUDGETS)
    assert len(rows) == 27 and rows.feasible.sum() == 26
    rows.loc[0, "gap"] = 0.0
    with pytest.raises(ValueError, match="undefined"):
        validate_budget_runs(rows, NAMES, SEEDS, BUDGETS)


def test_capacity_and_mst_are_valid_lower_bounds():
    inst = Instance(name="bound", coords=np.array([[0, 0], [1, 0], [2, 0]]),
                    demands=np.array([0, 2, 2]), capacity=2)
    bound = lower_bounds(inst)
    assert bound["mst_lower_bound"] == 2
    assert bound["vehicle_lower_bound"] == 2
    assert bound["lower_bound"] == 4
    assert bound["lower_bound"] <= Solution([[1], [2]]).cost(inst)


def test_mst_includes_zero_cost_edges_between_coincident_nodes():
    inst = Instance(name="duplicate", coords=np.array([[0, 0], [0, 0], [1, 0]]),
                    demands=np.array([0, 1, 1]), capacity=10)
    bound = lower_bounds(inst)
    assert bound["mst_lower_bound"] == 1
    assert bound["lower_bound"] <= Solution([[1, 2]]).cost(inst)
