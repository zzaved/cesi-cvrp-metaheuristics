"""Adapt the shared SA implementation to the Solomon comparison study.

The problem model, construction and independent evaluator are imported from
``cvrp.sa_vrptw``; no notebook cells are executed or copied.
"""

from __future__ import annotations

import numpy as np

from cvrp.instance import Instance
from cvrp.sa_static import anneal_static, warmup
from cvrp.sa_vrptw import Problem, initialize, validate

warmup()


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


def run_sa(inst: Instance, seed: int, time_limit: float) -> dict:
    """One SA run; ``time_limit`` includes the construction, as in Dag's notebook."""
    p = problem_from_instance(inst)
    return anneal_static(p, initialize, validate, seed=seed, time_limit=time_limit)
