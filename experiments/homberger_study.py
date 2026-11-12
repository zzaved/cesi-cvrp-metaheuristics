"""Independent, picklable SA jobs for the three-instance Homberger notebook study."""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
import vrplib

from cvrp.instance import Instance
from cvrp.sa import SAParams, sa
from cvrp.solution import Solution
from cvrp.utils import distance_matrix

DATA = Path(__file__).resolve().parents[1] / "data" / "homberger"


def names():
    """Return one R1 instance at each of the three requested customer counts."""
    return ["R1_4_1", "R1_8_1", "R1_10_1"]


def load(name, data=DATA):
    """Match the PyVRP reference's truncated Euclidean costs and zero depot service."""
    data = Path(data)
    inst = Instance.from_vrplib(
        data / f"{name}.vrp", data / f"{name}.sol", round_euc2d=False
    )
    inst.dist = distance_matrix(inst.coords, rounding="floor1")
    if inst.service_times is not None:
        inst.service_times[0] = 0.0
    return inst


def check_reference(name, data=DATA):
    """Independently validate coverage, constraints and the reported reference cost."""
    inst = load(name, data)
    raw = vrplib.read_solution(str(Path(data) / f"{name}.sol"))
    reference = Solution([list(route) for route in raw["routes"]])
    violations = reference.violations(inst)
    if violations:
        raise ValueError(f"Invalid reference for {name}: {violations}")
    cost = reference.cost(inst)
    if not math.isclose(cost, inst.best_known, abs_tol=1e-6, rel_tol=0):
        raise ValueError(f"Reference cost mismatch for {name}: {cost} != {inst.best_known}")
    return dict(
        instance=name, n=inst.n_customers, best_known=inst.best_known,
        reference_cost=cost, reference_routes=len(reference.routes), reference_feasible=True,
    )


def run_one(job):
    """Run SA from its own initialization, preserving failures with undefined gaps."""
    name, seed, params, limit = job
    inst = load(name)
    row = dict(
        instance=name, n=inst.n_customers, algorithm="sa", seed=seed,
        params=str(params), time_limit=limit, best_known=inst.best_known,
    )
    started = time.perf_counter()
    try:
        result = sa(inst, SAParams(time_limit=limit, **params), seed=seed)
    except RuntimeError as exc:
        return row | dict(
            cost=np.nan, gap=np.nan, feasible=False, seconds=time.perf_counter() - started,
            iterations=0, routes=np.nan, stop_reason="solver_error", error=str(exc),
        )
    feasible = result.best is not None and result.best.is_feasible(inst)
    cost = result.best.cost(inst) if feasible else np.nan
    return row | dict(
        cost=cost, gap=100 * (cost / inst.best_known - 1), feasible=feasible,
        seconds=result.runtime, iterations=result.iterations,
        routes=len(result.best.routes) if result.best is not None else np.nan,
        stop_reason=result.stop_reason, error="",
    )
