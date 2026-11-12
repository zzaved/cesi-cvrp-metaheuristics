"""GRASP beyond Solomon: Homberger, 10,000 customers, real cities, sensitivity (owner: Farida).

Every job is a picklable tuple run in a worker process, the same pattern as Dag's
``homberger_study.py``, and every row is checked with the shared ``Solution`` evaluator.
Used by notebook 04 (sections 10 to 13); results go to ``results/grasp_*.csv``.

Usage:
    python experiments/grasp_large_study.py homberger    # -> results/grasp_homberger.csv
    python experiments/grasp_large_study.py synthetic    # -> results/grasp_synthetic_10000.csv
    python experiments/grasp_large_study.py cities       # -> results/grasp_cities.csv
    python experiments/grasp_large_study.py intrinsic    # -> results/grasp_intrinsic.csv
    python experiments/grasp_large_study.py extrinsic    # -> results/grasp_extrinsic.csv
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT / "src", ROOT / "experiments"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from cvrp.cities import load_city  # noqa: E402
from cvrp.grasp import GRASPParams, grasp  # noqa: E402
from cvrp.instance import Instance  # noqa: E402
from cvrp.solution import Solution  # noqa: E402

RESULTS = ROOT / "results"
CITIES = ROOT / "data" / "cities"
CITY_FILES = {"Paris": CITIES / "Paris_data.npz", "Sao Paulo": CITIES / "Sao_Paulo_data.npz"}
WORKERS = int(os.environ.get("GRASP_WORKERS", max(1, min(7, (os.cpu_count() or 2) - 1))))

# Solomon campaign setting (section 6 of notebook 04): full VND passes, big kicks.
SOLOMON = dict(alpha=0.3, improvement="first", perturb_kicks=90)
# Large-instance settings: localized descent (don't-look bits) and small kicks.
#   GRASP     = multi-start only (construction + descent, no kicks)
#   GRASP-ILS = each start is improved by up to 300 kicks of at most 30 customers
LARGE = {
    "GRASP": dict(alpha=0.3, local_search="dlb", perturb_kicks=0),
    "GRASP-ILS": dict(alpha=0.3, local_search="dlb", perturb_kicks=300, kick_max=30),
}


# --------------------------------------------------------------------------- #
# Instances                                                                    #
# --------------------------------------------------------------------------- #
def homberger(name: str) -> Instance:
    """Homberger R1 instance with Dag's conventions (floor to 1 decimal, depot service 0)."""
    import homberger_study  # Dag's loader: same distances and references as his SA study

    return homberger_study.load(name)


def synthetic(
    n: int = 10_000, layout: str = "uniform", capacity: float = 100.0, graph_seed: int = 101
) -> Instance:
    """Same instance as section 11 of Dag's SA notebook (same generator, same seed).

    Customers uniform (or in 8 clusters) on [0, 100]^2, depot at (50, 50), demands 1..10,
    complete Euclidean distances. Dag also builds a NetworkX proximity graph on these points
    for display; routing uses the complete Euclidean matrix, which is what is rebuilt here.
    """
    from scipy.spatial.distance import cdist

    rng = np.random.default_rng(graph_seed)
    if layout == "uniform":
        customers = rng.uniform(0, 100, (n, 2))
    elif layout == "clustered":
        centers = rng.uniform(10, 90, (8, 2))
        customers = np.clip(centers[rng.integers(0, 8, n)] + rng.normal(0, 4, (n, 2)), 0, 100)
    else:
        raise ValueError(f"Unknown layout: {layout}")
    coords = np.vstack(([50.0, 50.0], customers))
    demands = np.r_[0.0, rng.integers(1, 11, n).astype(float)]
    return Instance(
        name=f"nx-{layout}-n{n}-q{capacity:g}-g{graph_seed}",
        coords=coords,
        demands=demands,
        capacity=capacity,
        dist=cdist(coords, coords),
    )


def sweep(inst: Instance) -> Solution:
    """Dag's capacity-feasible sweep start (the reference point of his 10,000 study)."""
    xy = inst.coords[1:] - inst.coords[0]
    order = np.argsort(np.arctan2(xy[:, 1], xy[:, 0])) + 1
    routes, route, load = [], [], 0.0
    for node in order:
        if route and load + inst.demands[node] > inst.capacity:
            routes.append(route)
            route, load = [], 0.0
        route.append(int(node))
        load += inst.demands[node]
    if route:
        routes.append(route)
    return Solution(routes)


def city(name: str, n: int, seed: int = 0, **kw) -> Instance:
    """Real road-network instance (see ``cvrp.cities.load_city``)."""
    return load_city(CITY_FILES[name], n=n, seed=seed, **kw)


def build(spec: dict) -> Instance:
    """Instance from a picklable description ``{"kind": ..., ...}``."""
    spec = dict(spec)
    kind = spec.pop("kind")
    if kind == "homberger":
        return homberger(spec["name"])
    if kind == "solomon":
        import solomon_study

        return solomon_study.load(spec["name"])
    if kind == "synthetic":
        return synthetic(**spec)
    if kind == "city":
        return city(**spec)
    raise ValueError(kind)


# --------------------------------------------------------------------------- #
# One run                                                                      #
# --------------------------------------------------------------------------- #
def run_one(job: tuple) -> dict:
    """``job = (study, label, instance spec, params, seed, time_limit)`` -> one result row."""
    study, label, spec, params, seed, limit = job
    inst = build(spec)
    kw = dict(params)
    kw.setdefault("iterations", 10**9)
    p = GRASPParams(time_limit=limit, **kw)
    res = grasp(inst, p, seed=seed)
    sol = res.best
    feasible = sol is not None and sol.is_feasible(inst)
    distance = sol.cost(inst) if feasible else np.nan
    h = res.history
    row = dict(
        study=study,
        label=label,
        instance=inst.name,
        n=inst.n_customers,
        params=str(params),
        seed=seed,
        time_limit=limit,
        cost=res.cost if feasible else np.nan,
        distance=distance,
        feasible=feasible,
        routes=len(sol.routes) if sol is not None else np.nan,
        min_routes=int(np.ceil(inst.demands.sum() / inst.capacity)),
        seconds=res.runtime,
        iterations=res.iterations,
        kicks=h[-1].get("kicks", 0) if h else 0,
        constructed=h[0]["constructed"] if h else np.nan,
        best_known=inst.best_known if inst.best_known is not None else np.nan,
    )
    row.update({k: v for k, v in spec.items() if k != "kind"})
    if inst.best_known is not None and feasible:
        row["gap"] = 100 * (distance / inst.best_known - 1)
    return row


def execute(jobs: list[tuple], workers: int = WORKERS) -> pd.DataFrame:
    """Run jobs in parallel worker processes (one CPU core left free)."""
    t0 = time.perf_counter()
    if workers <= 1:
        rows = [run_one(j) for j in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(run_one, jobs))
    print(f"{len(jobs)} runs in {time.perf_counter() - t0:.0f} s on {workers} workers")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Studies                                                                      #
# --------------------------------------------------------------------------- #
HOMBERGER = ["R1_4_1", "R1_8_1", "R1_10_1"]


def homberger_jobs(seeds=range(1, 11), limit: float = 20.0) -> list[tuple]:
    """Dag's protocol: 3 R1 instances x 10 seeds x 20 s, both GRASP variants."""
    return [
        ("homberger", v, {"kind": "homberger", "name": name}, LARGE[v], s, limit)
        for name in HOMBERGER
        for v in LARGE
        for s in seeds
    ]


def city_jobs(sizes=(100, 250, 500, 999), seeds=range(1, 6), limit: float = 20.0) -> list[tuple]:
    """Paris and São Paulo, road km, CVRP Q=100, same customer sample seed 0 for every run."""
    return [
        ("cities", v, {"kind": "city", "name": c, "n": n}, LARGE[v], s, limit)
        for c in CITY_FILES
        for n in sizes
        for v in LARGE
        for s in seeds
    ]


# Intrinsic factors = parameters of the algorithm (one factor at a time around the baseline).
INTRINSIC_BASE = dict(SOLOMON, n_neighbors=20, construction="regret", local_search="vnd")
INTRINSIC = {
    "alpha": [0.0, 0.1, 0.3, 0.5, 1.0],
    "perturb_kicks": [0, 30, 90, 250],
    "n_neighbors": [5, 10, 20, 40],
    "improvement": ["first", "best"],
    "construction": ["cheapest", "regret"],
    "local_search": ["vnd", "dlb"],
    "time_limit": [5.0, 10.0, 20.0],
}
INTRINSIC_INSTANCES = ["C101", "C201", "R101", "R201", "RC101", "RC201"]  # team tuning set
INTRINSIC_LIMIT = 10.0
# Large-instance intrinsic factors, on Homberger R1_4_1 (400 customers).
INTRINSIC_LARGE_BASE = dict(LARGE["GRASP-ILS"])
INTRINSIC_LARGE = {
    "kick_max": [15, 30, 60, 120],
    "perturb_kicks": [0, 30, 300, 3000],
    "local_search": ["vnd", "dlb"],
}


def _ofat(base: dict, factors: dict) -> list[tuple[str, object, dict]]:
    """(factor, value, setting) for every one-factor-at-a-time point (baseline repeated)."""
    out = []
    for name, values in factors.items():
        for v in values:
            out.append((name, v, {**base, name: v}))
    return out


def intrinsic_jobs(seeds=(101, 102)) -> list[tuple]:
    """Intrinsic study, one factor at a time: Solomon tuning set (10 s) and R1_4_1 (20 s)."""
    jobs, done = [], {}
    for name, v, setting in _ofat(INTRINSIC_BASE, INTRINSIC):
        limit = setting.pop("time_limit", INTRINSIC_LIMIT)
        key = (str(sorted(setting.items())), limit)
        if key in done:
            continue
        done[key] = True
        for inst in INTRINSIC_INSTANCES:
            for s in seeds:
                jobs.append(
                    (
                        "intrinsic",
                        f"{name}={v}",
                        {"kind": "solomon", "name": inst},
                        setting,
                        s,
                        limit,
                    )
                )
    for name, v, setting in _ofat(INTRINSIC_LARGE_BASE, INTRINSIC_LARGE):
        for s in (1, 2, 3):
            jobs.append(
                (
                    "intrinsic-large",
                    f"{name}={v}",
                    {"kind": "homberger", "name": "R1_4_1"},
                    setting,
                    s,
                    20.0,
                )
            )
    return jobs


# Extrinsic factors = properties of the instance and of the environment, GRASP-ILS fixed.
EXTRINSIC_LIMIT = 10.0


def extrinsic_jobs(seeds=(1, 2, 3)) -> list[tuple]:
    """Extrinsic study: instance and environment factors, GRASP-ILS fixed, 10 s per run."""
    ils = LARGE["GRASP-ILS"]
    pts: list[tuple[str, object, dict, dict]] = []
    for n in (100, 250, 500, 999):  # problem size
        pts.append(("customers n", n, {"kind": "city", "name": "Paris", "n": n}, ils))
    for q in (50, 100, 200):  # vehicle capacity
        pts.append(
            ("capacity Q", q, {"kind": "city", "name": "Paris", "n": 250, "capacity": q}, ils)
        )
    base_dur = {"kind": "city", "name": "Paris", "n": 250, "metric": "duration"}
    pts.append(("time windows", "none", base_dur, ils))
    for w in (240, 120, 60):  # time-window width (minutes)
        pts.append(
            (
                "time windows",
                f"{w} min",
                {**base_dur, "time_windows": True, "window_width": float(w)},
                ils,
            )
        )
    pts.append(("traffic", "none", base_dur, ils))
    for hour in (6, 8, 12, 17):  # depot departure under the hourly traffic profile
        pts.append(
            (
                "traffic",
                f"depart {hour}h",
                base_dur,
                {**ils, "objective": "duration", "start_min": 60.0 * hour},
            )
        )
    for layout in ("uniform", "clustered"):  # spatial distribution, synthetic n = 500
        pts.append(
            (
                "layout",
                layout,
                {"kind": "synthetic", "n": 500, "layout": layout, "graph_seed": 101},
                ils,
            )
        )
    for c in CITY_FILES:  # road network
        pts.append(("city", c, {"kind": "city", "name": c, "n": 250}, ils))
    return [
        ("extrinsic", f"{f}={v}", spec, params, s, EXTRINSIC_LIMIT)
        for f, v, spec, params in pts
        for s in seeds
    ]


def label_split(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``factor`` and ``value`` columns from ``label = "factor=value"``."""
    df = df.copy()
    df[["factor", "value"]] = df.label.str.split("=", n=1, expand=True)
    return df


if __name__ == "__main__":
    which = sys.argv[1]
    RESULTS.mkdir(exist_ok=True)
    jobs = {
        "homberger": homberger_jobs,
        "cities": city_jobs,
        "intrinsic": intrinsic_jobs,
        "extrinsic": extrinsic_jobs,
    }[which]()
    execute(jobs).to_csv(RESULTS / f"grasp_{which}.csv", index=False)
