"""Solution representation, cost and feasibility checks."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from cvrp.instance import Instance
from cvrp.timewindows import is_route_tw_feasible


def route_cost(route: list[int], dist: np.ndarray) -> float:
    """Return the travel cost of one route, depot to depot.

    Vectorized: one fancy-indexing gather instead of a Python loop.
    """
    if not route:
        return 0.0
    path = np.fromiter((0, *route, 0), dtype=np.intp, count=len(route) + 2)
    return float(dist[path[:-1], path[1:]].sum())


@dataclass
class Solution:
    """A set of routes. Each route lists customer indices, without the depot.

    Encoding chosen for the metaheuristic: a list of routes (giant tour with
    explicit separators is an alternative, see docs/technical/metaheuristic).
    """

    routes: list[list[int]] = field(default_factory=list)

    def copy(self) -> Solution:
        """Return a deep copy (routes are lists, so copy each one)."""
        return Solution([r.copy() for r in self.routes])

    def cost(self, inst: Instance) -> float:
        """Return the objective value: total travel cost of every route."""
        return sum(route_cost(r, inst.dist) for r in self.routes)

    def loads(self, inst: Instance) -> np.ndarray:
        """Return the load carried on each route."""
        return np.array([inst.demands[r].sum() if r else 0.0 for r in self.routes])

    def remove_empty_routes(self) -> None:
        """Drop routes with no customer, in place."""
        self.routes = [r for r in self.routes if r]

    def violations(self, inst: Instance) -> list[str]:
        """Return a human readable list of every broken constraint (empty if feasible)."""
        problems: list[str] = []
        visited = np.concatenate([np.asarray(r, dtype=int) for r in self.routes if r] or [[]])
        counts = np.bincount(visited.astype(int), minlength=inst.n_customers + 1)
        if counts[0] > 0:
            problems.append("depot appears inside a route")
        missing = np.flatnonzero(counts[1:] == 0) + 1
        repeated = np.flatnonzero(counts[1:] > 1) + 1
        if missing.size:
            problems.append(f"customers not visited: {missing.tolist()[:10]}")
        if repeated.size:
            problems.append(f"customers visited more than once: {repeated.tolist()[:10]}")
        over = np.flatnonzero(self.loads(inst) > inst.capacity + 1e-9)
        if over.size:
            problems.append(f"routes over capacity: {over.tolist()}")
        used = sum(1 for r in self.routes if r)
        if inst.num_vehicles is not None and used > inst.num_vehicles:
            problems.append(f"{used} routes used, fleet is {inst.num_vehicles}")
        if inst.has_time_windows:
            late = [i for i, r in enumerate(self.routes) if not is_route_tw_feasible(r, inst)]
            if late:
                problems.append(f"routes violating time windows: {late}")
        return problems

    def is_feasible(self, inst: Instance) -> bool:
        """Return True when no constraint is violated."""
        return not self.violations(inst)

    def __len__(self) -> int:
        """Return the number of non-empty routes."""
        return sum(1 for r in self.routes if r)
