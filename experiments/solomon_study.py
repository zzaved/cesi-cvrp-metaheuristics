"""Benchmark of Tabu Search on the 56 Solomon CVRPTW instances.

Protocol
- Instances: data/solomon/*.txt with their best known solution (*.sol), PyVRP/VRPLIB copy.
- Objective: total distance, travel time = distance, distances truncated to one decimal (the
  convention of the best known values), so gap = 100 (cost - BKS) / BKS is valid.
- Tuning set: the first instance of each class (C101, C201, R101, R201, RC101, RC201).
  Test set: the other 50. No test instance is used to choose a parameter.
- Same start (time-oriented nearest neighbor) and same time limit for every run.
- Other algorithms plug in through ``ALGORITHMS``: a function ``(inst, cost, params, seed)``
  returning an object with ``routes``, ``cost``, ``seconds`` and ``iterations``, and a tuning grid.
  They are then run on the same instances, objective, seeds and time limit.

Usage:
    python experiments/solomon_study.py tune   # -> results/solomon_tuning.csv
    python experiments/solomon_study.py run    # -> results/solomon_benchmark.csv
    python experiments/solomon_study.py tune grasp   # one algorithm only
    python experiments/solomon_study.py run grasp    # -> results/solomon_benchmark_grasp.csv
"""

from __future__ import annotations

import itertools
import os
import platform
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from types import SimpleNamespace  # noqa: E402

from cvrp.grasp import GRASPParams, grasp  # noqa: E402
from cvrp.instance import Instance  # noqa: E402
from cvrp.tabu import TabuParams, distance_cost, tabu_search  # noqa: E402
from cvrp.utils import distance_matrix  # noqa: E402

DATA = ROOT / "data" / "solomon"
RESULTS = ROOT / "results"
TIME_LIMIT = 20.0  # seconds per run
# parallel runs: one core left free, never more runs than cores (each run must get its 20 s)
WORKERS = max(1, min(7, (os.cpu_count() or 2) - 1))
TUNING = ["C101", "C201", "R101", "R201", "RC101", "RC201"]
TUNE_SEEDS = [101, 102]
TEST_SEEDS = list(range(1, 11))  # 10 seeds per (instance, algorithm)


def load(name: str) -> Instance:
    """Read a Solomon instance and its best known cost.

    The best known costs of this dataset use distances truncated to one decimal (checked on all
    56 files), so the instance uses the same distances; with exact distances every gap would be
    about 0.3 % too high.
    """
    inst = Instance.from_vrplib(
        DATA / f"{name}.txt", DATA / f"{name}.sol", instance_format="solomon"
    )
    inst.dist = distance_matrix(inst.coords, rounding="floor1")
    return inst


def _tabu(inst: Instance, cost, params: dict, seed: int):
    return tabu_search(inst, cost, TabuParams(time_limit=TIME_LIMIT, **params), seed)


def _grasp(inst: Instance, cost, params: dict, seed: int):
    """GRASP (Farida): restarts until the time limit; perturb_kicks > 0 = GRASP-ILS."""
    params = dict(params)
    limit = params.pop("time_limit", TIME_LIMIT)  # only overridden for quick notebook checks
    res = grasp(inst, GRASPParams(iterations=10**9, time_limit=limit, **params), seed=seed)
    if res.best is None or not res.best.is_feasible(inst):  # shared evaluator, time windows too
        raise RuntimeError(f"GRASP found no feasible solution on {inst.name}")
    return SimpleNamespace(
        routes=res.best.routes, cost=res.cost, seconds=res.runtime, iterations=res.iterations
    )


# name -> (solver, tuning grid)
ALGORITHMS = {
    "tabu": (_tabu, {"tenure": [5, 10, 20], "candidates": [50, 200, 500]}),
    "grasp": (
        _grasp,
        {"alpha": [0.1, 0.3, 0.5], "improvement": ["first", "best"], "perturb_kicks": [0, 90]},
    ),
}


def run_one(job: tuple[str, str, dict, int]) -> dict:
    """Run one (instance, algorithm, parameters, seed) and return one CSV row."""
    name, algo, params, seed = job
    inst = load(name)
    cost = distance_cost(inst)
    res = ALGORITHMS[algo][0](inst, cost, params, seed)
    served = sorted(c for r in res.routes for c in r) == list(range(1, inst.n_customers + 1))
    check = sum(cost(tuple(r)) for r in res.routes)
    return {
        "instance": name,
        "family": name.rstrip("0123456789"),
        "n": inst.n_customers,
        "time_windows": True,
        "algorithm": algo,
        "params": str(params),
        "seed": seed,
        "cost": round(res.cost, 2),
        "best_known": inst.best_known,
        "gap": round(100 * (res.cost - inst.best_known) / inst.best_known, 3),
        "seconds": round(res.seconds, 2),
        "iterations": res.iterations,
        "routes": len(res.routes),
        "feasible": served and abs(check - res.cost) < 1e-6,
    }


def grid(d: dict) -> list[dict]:
    """Every combination of the parameter values."""
    return [dict(zip(d, v, strict=True)) for v in itertools.product(*d.values())]


def run(jobs: list, out: Path) -> pd.DataFrame:
    """Run the jobs in parallel, saving the CSV every 25 runs."""
    RESULTS.mkdir(exist_ok=True)
    cpu = platform.processor()
    print(f"{len(jobs)} runs x {TIME_LIMIT:.0f} s on {WORKERS} workers, {cpu}", flush=True)
    rows = []
    with Pool(WORKERS) as pool:
        for i, row in enumerate(pool.imap_unordered(run_one, jobs), 1):
            rows.append(row)
            if i % 25 == 0 or i == len(jobs):
                pd.DataFrame(rows).to_csv(out, index=False)
                print(f"{i}/{len(jobs)}", flush=True)
    return pd.DataFrame(rows)


def best_params(tuning: pd.DataFrame, algo: str) -> dict:
    """Parameters with the lowest mean gap on the tuning set."""
    t = tuning[tuning.algorithm == algo].groupby("params").gap.mean()
    print(f"{algo} tuning (mean gap %):\n{t.sort_values().round(2).to_string()}")
    return eval(t.idxmin())  # noqa: S307  (our own str(dict))


def tune_jobs(algos: list[str]) -> list:
    """Every (tuning instance, algorithm, parameters, seed)."""
    return [
        (n, a, p, s)
        for a in algos
        for n in TUNING
        for p in grid(ALGORITHMS[a][1])
        for s in TUNE_SEEDS
    ]


def test_jobs(chosen: dict[str, dict]) -> list:
    """Every (test instance, algorithm, chosen parameters, seed)."""
    test = sorted(p.stem for p in DATA.glob("*.txt") if p.stem not in TUNING)
    return [(n, a, p, s) for n in test for a, p in chosen.items() for s in TEST_SEEDS]


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "run"
    only = sys.argv[2:]  # optional algorithm names, e.g. `run grasp`
    algos = only or list(ALGORITHMS)
    suffix = "_" + "_".join(only) if only else ""
    if phase == "tune":
        run(tune_jobs(algos), RESULTS / f"solomon_tuning{suffix}.csv")
    else:
        tuning = pd.read_csv(RESULTS / f"solomon_tuning{suffix}.csv")
        chosen = {a: best_params(tuning, a) for a in algos}
        run(test_jobs(chosen), RESULTS / f"solomon_benchmark{suffix}.csv")
