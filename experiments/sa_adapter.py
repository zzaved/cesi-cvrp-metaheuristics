"""Adapter that plugs Dag's compiled Simulated Annealing into the Solomon study.

``cvrp.sa_static.anneal_static`` expects a ``Problem`` object plus an ``initialize`` and a
``validate`` function, which live in ``notebooks/SA.ipynb``. This file copies those helpers
unchanged (same construction, same evaluator) and builds the ``Problem`` from the shared
``cvrp.Instance``, so SA reads exactly the same data, truncated distances and fleet limit as
Tabu Search and GRASP. ``src/cvrp/sa_static.py`` is not modified.

Objective: ``mode="distance"`` (vehicle weight 0), i.e. total distance only, the same
objective as the other two algorithms. The notebook's ``benchmark`` mode (vehicles first) is
not used, because it would optimize a different objective than Tabu and GRASP.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np

from cvrp.instance import Instance
from cvrp.sa_static import anneal_static, warmup

# Compile the numba kernels once per process, before any timed run.
warmup()


@dataclass
class Problem:
    """Same fields as ``Problem`` in notebooks/SA.ipynb."""

    name: str
    xy: np.ndarray
    q: np.ndarray
    tw: np.ndarray
    service: np.ndarray
    capacity: float
    max_vehicles: int
    distance: np.ndarray
    mode: str = "distance"
    departure_step: float = 15.0
    distance_convention: str = "truncated"

    @property
    def n(self) -> int:
        """Number of customers (the depot is node 0)."""
        return len(self.q) - 1


def problem_from_instance(inst: Instance) -> Problem:
    """Build the SA problem from the shared instance (same ``inst.dist``, travel = distance)."""
    n1 = len(inst.demands)
    service = (
        np.asarray(inst.service_times, dtype=float).copy()
        if inst.service_times is not None
        else np.zeros(n1)
    )
    service[0] = 0.0
    tw = np.column_stack([inst.ready_times, inst.due_times]).astype(float)
    return Problem(
        name=inst.name,
        xy=np.asarray(inst.coords, dtype=float),
        q=np.asarray(inst.demands, dtype=float),
        tw=tw,
        service=service,
        capacity=float(inst.capacity),
        max_vehicles=int(inst.num_vehicles) if inst.num_vehicles else inst.n_customers,
        distance=np.ascontiguousarray(inst.dist, dtype=float),
        mode="distance",
    )


# ---- Copied from notebooks/SA.ipynb (Dag), static modes only --------------------------------


def simulate(p, route, departure=0.0):
    """Independent forward schedule; None if infeasible."""
    if not route:
        return dict(distance=0.0, duration=0.0, departure=departure, return_time=departure)
    if sum(p.q[i] for i in route) > p.capacity + 1e-8:
        return None
    if departure < p.tw[0, 0] - 1e-8 or departure > p.tw[0, 1] + 1e-8:
        return None
    t, prev, distance = departure, 0, 0.0
    for j in list(route) + [0]:
        length = p.distance[prev, j]
        start = max(t + length, p.tw[j, 0])
        if start > p.tw[j, 1] + 1e-8:
            return None
        t = start + p.service[j]
        distance += length
        prev = j
    return dict(distance=distance, duration=t - departure, departure=departure, return_time=t)


def evaluate_route(p, route):
    """Route distance and schedule, or (inf, None) if a window or the capacity breaks."""
    if not route:
        return 0.0, None
    sch = simulate(p, route, p.tw[0, 0])
    if sch is None:
        return math.inf, None
    return sch["distance"], sch


def validate(p, routes):
    """Recompute from scratch: coverage, capacity, windows, fleet."""
    flat = [i for r in routes for i in r]
    assert sorted(flat) == list(range(1, p.n + 1)), "Missing/duplicate/out-of-range customer"
    routes = [r for r in routes if r]
    assert len(routes) <= p.max_vehicles, "Fleet limit exceeded"
    schedules = []
    for r in routes:
        assert sum(p.q[i] for i in r) <= p.capacity + 1e-8
        cost, sch = evaluate_route(p, r)
        assert math.isfinite(cost), "Time window/depot violation"
        schedules.append(sch)
    return dict(
        vehicles=len(routes),
        distance=sum(s["distance"] for s in schedules),
        duration=sum(s["duration"] for s in schedules),
    )


def repair(p, routes, removed, rng, route_limit=8, deadline=math.inf):
    """Randomized cheapest feasible insertion; a new route is permitted."""
    routes = [list(r) for r in routes if r]
    rng.shuffle(removed)
    for customer in removed:
        if time.perf_counter() >= deadline:
            raise TimeoutError("SA time budget exhausted")
        options = []
        candidates = sorted(
            range(len(routes)), key=lambda k: min(p.distance[customer, j] for j in routes[k])
        )[:route_limit]
        for k in candidates:
            r = routes[k]
            if sum(p.q[i] for i in r) + p.q[customer] > p.capacity + 1e-8:
                continue
            old, _ = evaluate_route(p, r)
            for pos in range(len(r) + 1):
                if time.perf_counter() >= deadline:
                    raise TimeoutError("SA time budget exhausted")
                nr = r[:pos] + [customer] + r[pos:]
                cost, _ = evaluate_route(p, nr)
                if math.isfinite(cost):
                    options.append((cost - old, k, nr))
        if options:
            options.sort(key=lambda x: x[0])
            choice = 0 if rng.random() < 0.9 else int(rng.integers(min(3, len(options))))
            _, k, nr = options[choice]
            routes[k] = nr
        elif len(routes) < p.max_vehicles and math.isfinite(evaluate_route(p, [customer])[0]):
            routes.append([customer])
        else:
            return None
    return routes


def initialize(p, rng, deadline=math.inf):
    """Feasible start built without any reference routes (up to 50 attempts)."""
    for _ in range(50):
        out = repair(p, [], list(range(1, p.n + 1)), rng, deadline=deadline)
        if out is not None:
            return out
    raise RuntimeError("No feasible initialization")


# ---- Entry point used by experiments/solomon_study.py ---------------------------------------


def run_sa(inst: Instance, seed: int, time_limit: float) -> dict:
    """One SA run; ``time_limit`` includes the construction, as in Dag's notebook."""
    p = problem_from_instance(inst)
    return anneal_static(p, initialize, validate, seed=seed, time_limit=time_limit)
