"""Pilot size on real roads: 300 customers of Paris and Sao Paulo, the full model of notebook 01.

Duration with hourly traffic and time windows (same windows as ``city_study``: depot day 8:00 to
18:00, 120 min per customer, 5 min of service), trucks leaving at 8:00; Tabu Search and GRASP-ILS
with their tuned settings, 60 s, 5 seeds. The ADEME pilot has a few hundred deliveries per depot,
so this checks which algorithm to recommend at that size, not only at 999 customers.

Usage:
    python experiments/city_pilot.py          # -> results/city_pilot.csv
    python experiments/city_pilot.py timing   # -> results/city_grasp_timing.csv
"""

from __future__ import annotations

import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

import city_study as cs  # noqa: E402

from cvrp.cities import load_city  # noqa: E402
from cvrp.grasp import GRASPParams, grasp  # noqa: E402
from cvrp.solution import Solution  # noqa: E402
from cvrp.tabu import duration_cost  # noqa: E402

N = 300
START = 480.0


def run_one(job: tuple) -> dict:
    """One (city, algorithm, seed) run on the 300 customer instance, checked independently."""
    city, algo, seed = job
    inst = load_city(cs.DATA / cs.CITIES[city], n=N, metric="duration", seed=0, time_windows=True)
    routes, reported, iterations = cs.solve(algo, inst, START, seed)
    routes = [list(map(int, r)) for r in routes if len(r)]
    cost = duration_cost(inst, start_min=START)
    checked = sum(cost(tuple(r)) for r in routes)
    return {
        "city": city,
        "n": N,
        "algorithm": algo,
        "seed": seed,
        "cost": round(checked, 3),
        "cost_matches": abs(checked - reported) <= 1e-6 * max(1.0, checked),
        "feasible": Solution(routes=routes).is_feasible(inst),
        "routes": len(routes),
        "iterations": iterations,
    }


def timing() -> pd.DataFrame:
    """Seconds of one GRASP-ILS construction plus first descent, static against hourly traffic.

    Paris with the windows above, 300 and 999 customers: the static mode checks windows with the
    cached times of each route; the traffic mode recomputes the duration of every candidate route.
    """
    rows = []
    for n in (N, None):
        inst = load_city(
            cs.DATA / cs.CITIES["Paris"], n=n, metric="duration", seed=0, time_windows=True
        )
        for objective in ("distance", "duration"):
            p = GRASPParams(
                alpha=0.3,
                improvement="first",
                perturb_kicks=0,
                iterations=1,
                objective=objective,
                start_min=START,
                time_limit=600.0,
            )
            t0 = time.perf_counter()
            grasp(inst, p, seed=1)
            rows.append(
                {
                    "customers": inst.n_customers,
                    "mode": "static" if objective == "distance" else "hourly traffic",
                    "construction_descent_s": round(time.perf_counter() - t0, 1),
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    if sys.argv[1:] == ["timing"]:
        t = timing()
        t.to_csv(cs.RESULTS / "city_grasp_timing.csv", index=False)
        print(t.to_markdown(index=False))
        sys.exit()
    jobs = [(c, a, s) for c in cs.CITIES for a in ("tabu", "grasp") for s in cs.SEEDS]
    with Pool(cs.WORKERS) as pool:
        rows = pool.map(run_one, jobs)
    out = pd.DataFrame(rows)
    out.to_csv(cs.RESULTS / "city_pilot.csv", index=False)
    print(
        out.groupby(["city", "algorithm"])
        .agg(
            mean=("cost", "mean"),
            best=("cost", "min"),
            iterations=("iterations", "mean"),
            ok=("feasible", "all"),
        )
        .round(1)
        .to_markdown()
    )
