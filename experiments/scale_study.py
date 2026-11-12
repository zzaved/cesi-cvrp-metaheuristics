"""Scale study: the three metaheuristics from 100 to 10 000 customers, on one machine.

Protocol:
- Homberger R1 instances with 400, 800 and 1 000 customers (time windows, data/homberger,
  same loader and truncated distances as experiments/homberger_study.py), budgets of 20, 60 and
  120 s, seeds 1 to 3. Gap to the best known solution.
- One uniform synthetic CVRP with 10 000 customers (no time windows), 300 s, seed 1, one run at
  a time (the 10 000 x 10 000 matrix takes 800 MB; parallel runs would swap on 8 GB).
  No best known solution exists, so quality is the gap to the best of the three runs and to a
  lower bound (minimum spanning tree, homberger_study.lower_bounds).
Every algorithm keeps the setting chosen by the Solomon tuning; every solution is checked by the
shared evaluator (coverage, capacity, time windows) and its cost is recomputed independently.

Usage:
    python experiments/scale_study.py homberger   # -> results/scale_homberger.csv
    python experiments/scale_study.py synthetic   # -> results/scale_synthetic.csv
    python experiments/scale_study.py synthetic grasp   # one algorithm, rows appended
    python experiments/scale_study.py sweep   # 1 000 to 5 000 uniform, 60 s -> scale_sweep.csv

At 10 000 customers a solver that checks its clock only between iterations can overrun the budget
by far; such a run is stopped at HARD_STOP times the budget and recorded as infeasible.
"""

from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool, TimeoutError
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import homberger_study  # noqa: E402
from sa_adapter import run_sa  # noqa: E402

from cvrp.grasp import GRASPParams, grasp  # noqa: E402
from cvrp.instance import Instance  # noqa: E402
from cvrp.solution import Solution  # noqa: E402
from cvrp.tabu import TabuParams, distance_cost, tabu_search  # noqa: E402
from cvrp.utils import distance_matrix  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"
WORKERS = max(1, min(7, (os.cpu_count() or 2) - 1))
ALGOS = ("tabu", "sa", "grasp")
SEEDS = (1, 2, 3)
BUDGETS = (20.0, 60.0, 120.0)
SYNTHETIC_N, SYNTHETIC_LIMIT = 10_000, 300.0
HARD_STOP = 2.0


def synthetic(n: int = SYNTHETIC_N, seed: int = 101) -> Instance:
    """Uniform customers on a 1 000 x 1 000 square, depot in the centre, demand 1 to 10, Q 100."""
    rng = np.random.default_rng(seed)
    coords = np.vstack([[500.0, 500.0], rng.uniform(0, 1000, size=(n, 2))])
    demands = np.concatenate([[0.0], rng.integers(1, 11, size=n).astype(float)])
    inst = Instance(name=f"U{n}", coords=coords, demands=demands, capacity=100.0)
    inst.dist = distance_matrix(coords)
    return inst


def solve(algo: str, inst: Instance, seed: int, limit: float):
    """Tuned setting of each algorithm; returns routes and iterations."""
    if algo == "tabu":
        p = TabuParams(tenure=20, candidates=200, time_limit=limit)
        r = tabu_search(inst, distance_cost(inst), p, seed)
        return r.routes, r.iterations
    if algo == "grasp":
        p = GRASPParams(
            alpha=0.3, improvement="first", perturb_kicks=90, iterations=10**9, time_limit=limit
        )
        r = grasp(inst, p, seed=seed)
        return (r.best.routes if r.best is not None else []), r.iterations
    r = run_sa(inst, seed, limit, initial_temperature_factor=0.01, final_temperature=0.005)
    return (r.best.routes if r.best is not None else []), r.iterations


def run_one(job: tuple) -> dict:
    """One (instance, algorithm, seed, budget) run, checked by the shared evaluator."""
    name, algo, seed, limit = job
    inst = synthetic(int(name[1:])) if name.startswith("U") else homberger_study.load(name)
    started = time.perf_counter()
    try:
        routes, iterations = solve(algo, inst, seed, limit)
        error = ""
    except Exception as exc:  # noqa: BLE001  a failure is a result at this scale
        routes, iterations, error = [], 0, f"{type(exc).__name__}: {exc}"
    seconds = time.perf_counter() - started
    sol = Solution(routes=[list(map(int, r)) for r in routes if len(r)])
    feasible = bool(sol.routes) and sol.is_feasible(inst)
    cost = sol.cost(inst) if feasible else np.nan
    bk = inst.best_known
    lb = homberger_study.lower_bounds(inst)["lower_bound"] if bk is None else np.nan
    return {
        "instance": name,
        "n": inst.n_customers,
        "algorithm": algo,
        "seed": seed,
        "time_limit": limit,
        "seconds": round(seconds, 2),
        "iterations": iterations,
        "feasible": feasible,
        "cost": round(cost, 2),
        "routes": len(sol.routes),
        "best_known": bk,
        "gap": round(100 * (cost / bk - 1), 3) if bk and feasible else np.nan,
        "lower_bound": round(lb, 2),
        "error": error,
    }


def homberger_jobs() -> list[tuple]:
    """Every (Homberger instance, algorithm, seed, budget)."""
    return [
        (i, a, s, b)
        for b in BUDGETS
        for i in homberger_study.names()
        for a in ALGOS
        for s in SEEDS
    ]


def synthetic_jobs(algos=ALGOS) -> list[tuple]:
    """One 10 000 customer run per algorithm (seed 1)."""
    return [(f"U{SYNTHETIC_N}", a, 1, SYNTHETIC_LIMIT) for a in algos]


SWEEP_N, SWEEP_LIMIT = (1_000, 2_000, 5_000), 60.0


def sweep_jobs() -> list[tuple]:
    """Uniform CVRP without windows from 1 000 to 5 000 customers: where each method stops."""
    return [(f"U{n}", a, 1, SWEEP_LIMIT) for n in SWEEP_N for a in ALGOS]


def run_guarded(job: tuple) -> dict:
    """run_one in its own process, stopped at HARD_STOP times the budget."""
    name, algo, seed, limit = job
    with Pool(1) as pool:
        try:
            return pool.apply_async(run_one, (job,)).get(timeout=HARD_STOP * limit + 60)
        except TimeoutError:
            pool.terminate()
    return {
        "instance": name,
        "n": int(name[1:]),
        "algorithm": algo,
        "seed": seed,
        "time_limit": limit,
        "seconds": HARD_STOP * limit + 60,
        "iterations": 0,
        "feasible": False,
        "cost": np.nan,
        "routes": 0,
        "best_known": None,
        "gap": np.nan,
        "lower_bound": np.nan,
        "error": f"stopped after {HARD_STOP * limit + 60:.0f} s",
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "homberger"
    out = RESULTS / f"scale_{cmd}.csv"
    if cmd == "homberger":
        rows, all_jobs = [], homberger_jobs()
        results = Pool(WORKERS).imap_unordered(run_one, all_jobs)
    else:  # one run at a time, appended to the existing rows of other algorithms
        algos = sys.argv[2:] or ALGOS
        old = pd.read_csv(out) if out.exists() and sys.argv[2:] else pd.DataFrame()
        rows = old[~old.algorithm.isin(algos)].to_dict("records") if len(old) else []
        all_jobs = sweep_jobs() if cmd == "sweep" else synthetic_jobs(algos)
        results = map(run_guarded, all_jobs)
    print(f"{len(all_jobs)} runs -> {out.name}", flush=True)
    for i, row in enumerate(results, 1):
        rows.append(row)
        pd.DataFrame(rows).to_csv(out, index=False)
        print(
            f"{i}/{len(all_jobs)} {row['instance']} {row['algorithm']} {row['time_limit']:.0f}s"
            f" cost={row['cost']} gap={row['gap']} ok={row['feasible']} {row['error']}",
            flush=True,
        )
