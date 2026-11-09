"""Exact approach study: how far the ILPs of src/cvrp/ilp.py go, and their bounds.

Three experiments, one CSV each, all with HiGHS on one thread and a fixed time limit:

1. ``exact_cvrp.csv``: the three CVRP formulations (MTZ, flow, capacity cuts) on the first n
   customers of A-n32-k5 and B-n31-k5, n = 6 to 16.
2. ``exact_cvrptw.csv``: the CVRPTW model (distance, no traffic) on the first n customers of
   C101, R101 and RC101 (truncated distances), n = 5 to 100, with its LP relaxation (lower
   bound) and Tabu Search (upper bound, 5 s) on the same sub-instance.
3. ``exact_traffic.csv``: the model of notebook 01 (route duration with hourly traffic) on the
   first n customers of C101, R101 and RC101, with time 0 of the instance placed at 8:00 and
   the hourly profile repeated over two days (the C1 working day ends after midnight).

Usage:
    python experiments/exact_study.py           # -> results/exact_*.csv
    python experiments/exact_study.py traffic   # one experiment only
"""

from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cvrp.ilp import (  # noqa: E402
    solve_cvrp_flow,
    solve_cvrp_mtz,
    solve_cvrp_rcc,
    solve_cvrptw,
    solve_tdvrptw,
)
from cvrp.instance import Instance  # noqa: E402
from cvrp.tabu import RHO, TabuParams, distance_cost, tabu_search  # noqa: E402
from cvrp.utils import distance_matrix  # noqa: E402

RESULTS = ROOT / "results"
LIMIT = 60.0  # seconds per exact solve
FORMULATIONS = {"MTZ": solve_cvrp_mtz, "flow": solve_cvrp_flow, "capacity cuts": solve_cvrp_rcc}
DAY_START = 480.0  # time 0 of a Solomon instance is 8:00 in the traffic experiment


def fresh(solve, *args, **kwargs):
    """Run one solve in a new process: in a long process HiGHS stopped before its time limit."""
    with ProcessPoolExecutor(max_workers=1, max_tasks_per_child=1) as pool:
        return pool.submit(solve, *args, **kwargs).result()


def head(inst: Instance, n: int, fleet: int | None = None) -> Instance:
    """The depot and the first n customers of an instance, same data otherwise."""
    keep = list(range(n + 1))

    def cut(a: np.ndarray | None) -> np.ndarray | None:
        return None if a is None else np.asarray(a)[keep].copy()

    return Instance(
        name=f"{inst.name}[:{n}]",
        coords=inst.coords[keep],
        demands=inst.demands[keep],
        capacity=inst.capacity,
        num_vehicles=fleet if fleet is not None else inst.num_vehicles,
        ready_times=cut(inst.ready_times),
        due_times=cut(inst.due_times),
        service_times=cut(inst.service_times),
        dist=inst.dist[np.ix_(keep, keep)].copy(),
    )


def solomon(name: str) -> Instance:
    """A Solomon instance with distances truncated to one decimal (the BKS convention)."""
    path = ROOT / "data" / "solomon" / f"{name}.txt"
    inst = Instance.from_vrplib(path, instance_format="solomon")
    inst.dist = distance_matrix(inst.coords, rounding="floor1")
    return inst


def row(inst: Instance, model: str, res, lp=None, **extra) -> dict:
    """One CSV line: status, best value (upper bound), proven bound, LP bound, size, time."""
    return {
        "instance": inst.name,
        "n": inst.n_customers,
        "model": model,
        "status": res.status,
        "objective": res.objective,
        "bound": res.lower_bound,
        "lp_bound": None if lp is None else lp.lower_bound,
        "seconds": round(res.seconds, 3),
        "variables": res.n_vars,
        "constraints": res.n_constraints,
        "feasible": res.solution is not None and res.solution.is_feasible(inst),
        **extra,
    }


def cvrp() -> pd.DataFrame:
    """Experiment 1: CVRP formulations against n."""
    rows = []
    cases = [("A", "A-n32-k5"), ("B", "B-n31-k5")]
    for family, name in cases:
        full = Instance.from_vrplib(ROOT / "data" / "cvrplib" / family / f"{name}.vrp")
        for n in range(6, 17, 2):
            inst = head(full, n, fleet=n)
            for label, solve in FORMULATIONS.items():
                res = fresh(solve, inst, time_limit=LIMIT)
                lp = fresh(solve, inst, time_limit=LIMIT, relax=True)
                rows.append(row(inst, label, res, lp))
                print(rows[-1]["instance"], label, res.status, f"{res.seconds:.1f}s", flush=True)
    return pd.DataFrame(rows)


def cvrptw() -> pd.DataFrame:
    """Experiment 2: CVRPTW model against n, with LP and Tabu bounds."""
    rows = []
    for name in ["C101", "R101", "RC101"]:
        full = solomon(name)
        for n in [5, 10, 15, 20, 25, 50, 75, 100]:
            inst = head(full, n, fleet=n)
            res = fresh(solve_cvrptw, inst, time_limit=LIMIT)
            lp = fresh(solve_cvrptw, inst, time_limit=LIMIT, relax=True)
            ts = tabu_search(inst, distance_cost(inst), TabuParams(time_limit=5.0), seed=1)
            rows.append(row(inst, "CVRPTW", res, lp, tabu=round(ts.cost, 2)))
            print(rows[-1]["instance"], res.status, f"{res.seconds:.1f}s", flush=True)
    return pd.DataFrame(rows)


def traffic() -> pd.DataFrame:
    """Experiment 3: the notebook 01 model (duration with traffic) against n."""
    rows = []
    for name in ["C101", "R101", "RC101"]:
        full = solomon(name)
        for n in range(3, 11):
            inst = head(full, n, fleet=n)
            inst.ready_times = inst.ready_times + DAY_START
            inst.due_times = inst.due_times + DAY_START
            res = fresh(solve_tdvrptw, inst, RHO * 2, time_limit=LIMIT)
            lp = fresh(solve_tdvrptw, inst, RHO * 2, time_limit=LIMIT, relax=True)
            rows.append(row(inst, "duration with traffic", res, lp))
            print(rows[-1]["instance"], res.status, f"{res.seconds:.1f}s", flush=True)
    return pd.DataFrame(rows)


EXPERIMENTS = {"cvrp": cvrp, "cvrptw": cvrptw, "traffic": traffic}

if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    for label in sys.argv[1:] or list(EXPERIMENTS):
        experiment = EXPERIMENTS[label]
        experiment().to_csv(RESULTS / f"exact_{label}.csv", index=False)
