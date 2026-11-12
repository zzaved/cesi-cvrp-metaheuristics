"""SA-only temperature selection and separate test-set benchmarking in memory."""

from __future__ import annotations

import ast
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from cvrp.sa_static import warmup

_STUDY_LIMIT = object()


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


def tuning_jobs(
    study, quick_check=False, *, seeds=None, time_limit=_STUDY_LIMIT, iterations=None
):
    """Use the reserved tuning grid, optionally overriding seeds and run budgets."""
    limit = (
        (1.0 if quick_check else study.TIME_LIMIT)
        if time_limit is _STUDY_LIMIT else time_limit
    )
    jobs = study.tune_jobs(["sa"])
    if seeds is None:
        seeds = study.TUNE_SEEDS[:1] if quick_check else study.TUNE_SEEDS
        jobs = [job for job in jobs if job[3] in seeds]
    else:
        jobs = [
            (n, a, p, seed)
            for n, a, p, original_seed in jobs
            if original_seed == study.TUNE_SEEDS[0]
            for seed in seeds
        ]
    budget = {} if iterations is None else {"iterations": iterations}
    return [(n, a, dict(p, time_limit=limit, **budget), s) for n, a, p, s in jobs]


def choose_parameters(tuning):
    """Select the lowest mean tuning gap; test results never participate in selection."""
    if tuning.empty or not tuning.feasible.eq(True).all():
        raise ValueError("Tuning must contain only feasible runs")
    ranking = tuning.groupby("params", sort=True).gap.mean().sort_values(kind="stable")
    chosen = ast.literal_eval(ranking.index[0])
    chosen.pop("time_limit", None)
    chosen.pop("iterations", None)
    return chosen, ranking.rename("mean_gap").reset_index()


def benchmark_jobs(
    study, chosen, quick_check=False, names=None, *, seeds=None,
    time_limit=_STUDY_LIMIT, iterations=None,
):
    """Run the other fifty instances, excluding the six parameter-selection cases."""
    if seeds is None:
        seeds = study.TEST_SEEDS[:2] if quick_check else study.TEST_SEEDS
    limit = (
        (1.0 if quick_check else study.TIME_LIMIT)
        if time_limit is _STUDY_LIMIT else time_limit
    )
    names = (
        sorted(p.stem for p in study.DATA.glob("*.txt") if p.stem not in study.TUNING)
        if names is None
        else names
    )
    budget = {} if iterations is None else {"iterations": iterations}
    return [
        (n, "sa", dict(chosen, time_limit=limit, **budget), seed)
        for n in names for seed in seeds
    ]


def validate_runs(rows, names, seeds, *, algorithm="sa", time_limit=20.0, iterations=None):
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
    if time_limit is None:
        if iterations is None or iterations <= 0:
            raise ValueError("Untimed validation requires a positive iteration budget")
        if not rows.iterations.eq(iterations).all():
            raise ValueError("Run did not complete its iteration budget")
        if "params" not in rows:
            raise ValueError("Untimed validation requires recorded run parameters")
        for raw in rows.params:
            params = ast.literal_eval(raw)
            if "time_limit" not in params or params["time_limit"] is not None:
                raise ValueError("Expected an explicitly disabled time limit")
            if params.get("iterations") != iterations:
                raise ValueError("Recorded iteration budget does not match the requested run")
    elif rows.seconds.lt(time_limit - 0.02).any():
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
