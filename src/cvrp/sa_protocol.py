"""SA-only temperature selection and separate test-set benchmarking in memory."""

from __future__ import annotations

import ast
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from cvrp.sa_static import warmup


def execute_jobs(jobs, runner, workers):
    """Execute shared-protocol jobs in memory, with compilation outside the run timer."""
    if workers < 1:
        raise ValueError("workers must be positive")
    if workers == 1:
        warmup()
        rows = [runner(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=warmup) as pool:
            rows = list(pool.map(runner, jobs))
    return pd.DataFrame(rows)


def tuning_jobs(study, quick_check=False):
    """Use the team's six tuning instances, grid and tuning seeds verbatim."""
    seeds = study.TUNE_SEEDS[:1] if quick_check else study.TUNE_SEEDS
    limit = 1.0 if quick_check else study.TIME_LIMIT
    return [
        (n, a, dict(p, time_limit=limit), s)
        for n, a, p, s in study.tune_jobs(["sa"])
        if s in seeds
    ]


def choose_parameters(tuning):
    """Select the lowest mean tuning gap; test results never participate in selection."""
    if tuning.empty or not tuning.feasible.eq(True).all():
        raise ValueError("Tuning must contain only feasible runs")
    ranking = tuning.groupby("params", sort=True).gap.mean().sort_values(kind="stable")
    chosen = ast.literal_eval(ranking.index[0])
    chosen.pop("time_limit", None)
    return chosen, ranking.rename("mean_gap").reset_index()


def benchmark_jobs(study, chosen, quick_check=False, names=None):
    """Run the other fifty instances, excluding the six parameter-selection cases."""
    seeds = study.TEST_SEEDS[:2] if quick_check else study.TEST_SEEDS
    limit = 1.0 if quick_check else study.TIME_LIMIT
    names = (
        sorted(p.stem for p in study.DATA.glob("*.txt") if p.stem not in study.TUNING)
        if names is None
        else names
    )
    return [(n, "sa", dict(chosen, time_limit=limit), seed) for n in names for seed in seeds]


def validate_runs(rows, names, seeds, *, algorithm="sa", time_limit=20.0):
    """Reject incomplete, quick, infeasible or differently seeded SA benchmark data."""
    required = {
        "instance",
        "algorithm",
        "seed",
        "cost",
        "best_known",
        "gap",
        "seconds",
        "iterations",
        "routes",
        "feasible",
    }
    missing = required - set(rows)
    if missing:
        raise ValueError(f"Missing benchmark columns: {sorted(missing)}")
    if not rows.algorithm.eq(algorithm).all():
        raise ValueError(f"Expected only {algorithm} rows")
    if rows.duplicated(["instance", "seed"]).any():
        raise ValueError("Duplicate instance/seed pairs")
    expected = {(n, s) for n in names for s in seeds}
    actual = set(zip(rows.instance, rows.seed, strict=True))
    if actual != expected:
        raise ValueError("Instance/seed pairs do not match the requested benchmark protocol")
    if not rows.feasible.astype(str).str.lower().eq("true").all():
        raise ValueError("Benchmark contains infeasible runs")
    numeric = rows[["cost", "best_known", "gap", "seconds", "iterations"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Non-finite benchmark values")
    if rows.best_known.le(0).any() or rows.iterations.le(0).any():
        raise ValueError("Reference costs and iteration counts must be positive")
    if rows.seconds.lt(time_limit - 0.02).any():
        raise ValueError("Runtime indicates a quick or shorter-budget run")
    gaps = 100 * (rows.cost / rows.best_known - 1)
    if not np.allclose(gaps, rows.gap, atol=0.001, rtol=0):
        raise ValueError("Gaps do not match cost and reference distance")


def summarize(rows):
    """Summarize per-instance distance, gap, runtime and iteration dispersion."""
    return (
        rows.groupby("instance")
        .agg(
            BKS=("best_known", "first"),
            best=("cost", "min"),
            mean=("cost", "mean"),
            distance_std=("cost", "std"),
            gap_best=("gap", "min"),
            gap_mean=("gap", "mean"),
            gap_std=("gap", "std"),
            routes=("routes", "mean"),
            seconds=("seconds", "mean"),
            seconds_std=("seconds", "std"),
            iterations=("iterations", "mean"),
            iterations_std=("iterations", "std"),
        )
        .reset_index()
    )
