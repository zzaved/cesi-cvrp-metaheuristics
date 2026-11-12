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


def lower_bounds(inst):
    """Return MST and capacity-aware depot-edge distance lower bounds.

    A route union connects all nodes, so its cost is at least the MST cost.
    Capacity requires at least ceil(total demand / capacity) nonempty routes;
    each contributes two depot edges costing at least the cheapest depot edge.
    Both relax time windows. Prim's dense implementation supports zero-cost
    edges and does not assume that truncated distances satisfy the triangle inequality.
    """
    if inst.n_customers == 0:
        return dict(mst_lower_bound=0.0, vehicle_lower_bound=0,
                    depot_edge_lower_bound=0.0, lower_bound=0.0)
    used = np.zeros(inst.n_customers + 1, dtype=bool)
    used[0] = True
    nearest = inst.dist[0].copy()
    nearest[0] = np.inf
    mst = 0.0
    for _ in range(inst.n_customers):
        node = int(np.argmin(nearest))
        if not np.isfinite(nearest[node]):
            raise ValueError("The routing graph is disconnected")
        mst += float(nearest[node])
        used[node] = True
        nearest = np.minimum(nearest, inst.dist[node])
        nearest[used] = np.inf
    vehicles = inst.lower_bound_vehicles
    depot_edges = 2 * vehicles * float(inst.dist[0, 1:].min())
    return dict(mst_lower_bound=mst, vehicle_lower_bound=vehicles,
                depot_edge_lower_bound=depot_edges, lower_bound=max(mst, depot_edges))


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
    ) | lower_bounds(inst)


def run_one(job):
    """Run SA from its own initialization, preserving failures with undefined gaps."""
    name, seed, params, limit = job
    inst = load(name)
    row = dict(
        instance=name, n=inst.n_customers, algorithm="sa", seed=seed,
        params=str(params), time_limit=limit, best_known=inst.best_known,
    ) | lower_bounds(inst)
    started = time.perf_counter()
    cpu_started = time.process_time()
    try:
        result = sa(inst, SAParams(time_limit=limit, **params), seed=seed)
    except RuntimeError as exc:
        return row | dict(
            cost=np.nan, gap=np.nan, feasible=False, seconds=time.perf_counter() - started,
            iterations=0, routes=np.nan, stop_reason="solver_error", error=str(exc),
            cpu_seconds=time.process_time() - cpu_started,
            time_to_best=np.nan, iteration_at_best=np.nan, gap_lb=np.nan,
        )
    cpu_seconds = time.process_time() - cpu_started
    feasible = result.best is not None and result.best.is_feasible(inst)
    cost = result.best.cost(inst) if feasible else np.nan
    return row | dict(
        cost=cost, gap=100 * (cost / inst.best_known - 1), feasible=feasible,
        seconds=result.runtime, iterations=result.iterations,
        routes=len(result.best.routes) if result.best is not None else np.nan,
        stop_reason=result.stop_reason, error="", cpu_seconds=cpu_seconds,
        time_to_best=result.history[-1]["seconds"] if feasible else np.nan,
        iteration_at_best=result.history[-1]["iteration"] if feasible else np.nan,
        gap_lb=100 * (cost / row["lower_bound"] - 1) if row["lower_bound"] > 0 else np.nan,
    )


def validate_budget_runs(rows, instance_names, seeds, budgets):
    """Validate a complete budget comparison without discarding unsuccessful seeds."""
    required = {
        "instance", "seed", "time_limit", "params", "best_known", "cost", "gap",
        "seconds", "iterations", "feasible", "stop_reason",
    }
    missing = required - set(rows)
    if missing:
        raise ValueError(f"Missing Homberger columns: {sorted(missing)}")
    keys = ["instance", "seed", "time_limit"]
    expected = {
        (name, seed, limit) for name in instance_names for seed in seeds for limit in budgets
    }
    actual = set(rows[keys].itertuples(index=False, name=None))
    if rows.duplicated(keys).any() or actual != expected:
        raise ValueError("Instance/seed/budget combinations are incomplete or duplicated")
    if rows.params.nunique() != 1:
        raise ValueError("Temperature parameters must stay fixed across budgets")
    if not np.isfinite(rows.best_known).all() or rows.best_known.le(0).any():
        raise ValueError("Reference costs must be finite and positive")
    successful = rows[rows.feasible.eq(True)]
    if not np.isfinite(successful[["cost", "gap", "seconds", "iterations"]]).all().all():
        raise ValueError("Non-finite values in successful runs")
    if successful.iterations.le(0).any():
        raise ValueError("Successful runs must contain proposed moves")
    if not successful.stop_reason.eq("time_limit").all():
        raise ValueError("Successful runs must stop at the requested time budget")
    if successful.seconds.lt(successful.time_limit - 0.02).any():
        raise ValueError("Successful run ended before its requested time budget")
    gaps = 100 * (successful.cost / successful.best_known - 1)
    if not np.allclose(successful.gap, gaps, atol=1e-6, rtol=0):
        raise ValueError("Homberger gaps do not match costs and references")
    if "time_to_best" in rows:
        if successful.time_to_best.lt(0).any() or (
            successful.time_to_best > successful.seconds
        ).any():
            raise ValueError("Time to observed best must be within measured runtime")
    if "lower_bound" in rows:
        if rows.lower_bound.lt(0).any() or (rows.lower_bound > rows.best_known + 1e-6).any():
            raise ValueError("Invalid distance lower bound")
    failed = rows[~rows.feasible.eq(True)]
    if failed.cost.notna().any() or failed.gap.notna().any():
        raise ValueError("Unsuccessful runs must have undefined distance and gap")
