"""Real cities: the three metaheuristics on the road networks of Paris and Sao Paulo.

Instances: the RRNCO files of Farida's ``cvrp.cities.load_city`` (999 real customers per city,
road distances and free-flow times from OSRM on OpenStreetMap, asymmetric). Same demands and
capacity rule as the synthetic instances, so the two cities differ only by their roads.

Objectives:
- ``distance``: total road distance in km; Tabu Search, GRASP-ILS and SA.
- ``duration 08:00`` and ``duration 22:00``: total route duration in minutes with the hourly
  traffic of notebook 01, all trucks leaving at 8:00 or at 22:00 (the night); Tabu Search and
  GRASP-ILS (the public SA solver has the distance objective only).

Every run uses the tuned setting of section 8.1, the same time limit and 5 seeds. The reported
cost is recomputed from the routes with the shared evaluator (distance) or with
``tabu.duration_cost`` (duration): a mismatch would mean that a move delta assumes a symmetric
matrix. Without a best known value, the deviation is measured to the best run of any algorithm on
the same city and objective.

Usage:
    python experiments/city_study.py run       # -> results/city_benchmark.csv
    python experiments/city_study.py metrics   # -> results/city_metrics.csv
    python experiments/city_study.py report
"""

from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from sa_adapter import run_sa  # noqa: E402

from cvrp.cities import load_city  # noqa: E402
from cvrp.grasp import GRASPParams, grasp  # noqa: E402
from cvrp.solution import Solution  # noqa: E402
from cvrp.tabu import TabuParams, distance_cost, duration_cost, tabu_search  # noqa: E402

CITIES = {"Paris": "Paris_data.npz", "Sao_Paulo": "Sao_Paulo_data.npz"}
DATA = ROOT / "data" / "cities"
RESULTS = ROOT / "results"
TIME_LIMIT = 60.0
SEEDS = [1, 2, 3, 4, 5]
WORKERS = 7
OBJECTIVES = {"distance": None, "duration 08:00": 480.0, "duration 22:00": 1320.0}
ALGOS = {"distance": ["tabu", "grasp", "sa"], "duration": ["tabu", "grasp"]}


def instance(city: str, objective: str):
    """The 999 customer instance of a city, in km or in free-flow minutes."""
    metric = "distance" if objective == "distance" else "duration"
    return load_city(DATA / CITIES[city], n=None, metric=metric, seed=0)


def solve(algo: str, inst, start: float | None, seed: int) -> tuple[list[list[int]], float, int]:
    """Run one algorithm with its tuned setting; return routes, reported cost, iterations."""
    if algo == "tabu":
        cost = distance_cost(inst) if start is None else duration_cost(inst, start_min=start)
        p = TabuParams(tenure=20, candidates=200, k_near=15, time_limit=TIME_LIMIT)
        r = tabu_search(inst, cost, p, seed)
        return r.routes, r.cost, r.iterations
    if algo == "grasp":
        p = GRASPParams(
            alpha=0.3,
            improvement="first",
            perturb_kicks=90,
            iterations=10**9,
            time_limit=TIME_LIMIT,
            objective="distance" if start is None else "duration",
            start_min=480.0 if start is None else start,
        )
        r = grasp(inst, p, seed=seed)
        return r.best.routes, r.cost, r.iterations
    r = run_sa(inst, seed, TIME_LIMIT, initial_temperature_factor=0.005, final_temperature=0.005)
    return r.best.routes, r.cost, r.iterations


def run_one(job: tuple[str, str, str, int]) -> dict:
    """One (city, objective, algorithm, seed) run, checked by an independent evaluation."""
    city, objective, algo, seed = job
    inst = instance(city, objective)
    start = OBJECTIVES[objective]
    routes, reported, iterations = solve(algo, inst, start, seed)
    routes = [list(map(int, r)) for r in routes if len(r)]
    sol = Solution(routes=routes)
    if start is None:
        checked = sol.cost(inst)
    else:
        duration = duration_cost(inst, start_min=start)
        checked = sum(duration(tuple(r)) for r in routes)
    return {
        "city": city,
        "objective": objective,
        "algorithm": algo,
        "seed": seed,
        "cost": round(checked, 3),
        "reported": round(reported, 3),
        "cost_matches": abs(checked - reported) <= 1e-6 * max(1.0, abs(checked)),
        "feasible": sol.is_feasible(inst),
        "routes": len(routes),
        "iterations": iterations,
    }


def jobs() -> list[tuple[str, str, str, int]]:
    """Every run of the study."""
    return [
        (city, objective, algo, seed)
        for city in CITIES
        for objective in OBJECTIVES
        for algo in ALGOS["distance" if objective == "distance" else "duration"]
        for seed in SEEDS
    ]


def haversine_km(points: np.ndarray) -> np.ndarray:
    """Straight line (great circle) distance between every pair of (lat, lon) points."""
    lat, lon = np.radians(points[:, 0]), np.radians(points[:, 1])
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def metrics() -> pd.DataFrame:
    """Numbers that describe each road network, computed from its matrices."""
    rows = []
    for city, file in CITIES.items():
        f = np.load(DATA / file)
        km, minutes = f["distance"], f["duration"]
        off = ~np.eye(len(km), dtype=bool)
        line = haversine_km(f["points"])
        near = line[off] > 0.05  # pairs at least 50 m apart, for the ratios
        rows.append(
            {
                "city": city,
                "area_km2": float(np.ptp(f["points"][:, 0]) * 110.57)
                * float(
                    np.ptp(f["points"][:, 1])
                    * 111.32
                    * np.cos(np.radians(f["points"][:, 0].mean()))
                ),
                "mean_trip_km": km[off].mean(),
                "mean_trip_min": minutes[off].mean(),
                "mean_speed_kmh": 60 * km[off].sum() / minutes[off].sum(),
                "circuity": np.median(km[off][near] / line[off][near]),
                "asymmetry_pct": 100 * np.abs(km - km.T)[off].mean() / km[off].mean(),
                "asymmetric_pairs_pct": 100 * (np.abs(km - km.T)[off] > 0.01).mean(),
            }
        )
    return pd.DataFrame(rows)


def report() -> None:
    """Deviation to the best run per city and objective, per algorithm."""
    b = pd.read_csv(RESULTS / "city_benchmark.csv")
    print("checks:", b.feasible.all(), "feasible,", b.cost_matches.all(), "costs match")
    best = b.groupby(["city", "objective"]).cost.transform("min")
    b["dev"] = 100 * (b.cost - best) / best
    t = b.groupby(["city", "objective", "algorithm"]).agg(
        mean_cost=("cost", "mean"),
        best_cost=("cost", "min"),
        mean_dev=("dev", "mean"),
        seed_std=("dev", "std"),
        routes=("routes", "mean"),
        iterations=("iterations", "mean"),
    )
    print(t.round(2).to_markdown())


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "metrics":
        m = metrics()
        m.to_csv(RESULTS / "city_metrics.csv", index=False)
        print(m.round(3).to_markdown(index=False))
    elif cmd == "report":
        report()
    else:
        all_jobs = jobs()
        print(f"{len(all_jobs)} runs x {TIME_LIMIT:.0f} s on {WORKERS} workers", flush=True)
        rows = []
        with Pool(WORKERS) as pool:
            for i, row in enumerate(pool.imap_unordered(run_one, all_jobs), 1):
                rows.append(row)
                pd.DataFrame(rows).to_csv(RESULTS / "city_benchmark.csv", index=False)
                print(
                    f"{i}/{len(all_jobs)} {row['city']} {row['objective']} {row['algorithm']}"
                    f" {row['cost']} ok={row['feasible'] and row['cost_matches']}",
                    flush=True,
                )
