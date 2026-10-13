"""Initial solutions: nearest neighbor, Clarke and Wright savings, sweep."""

from __future__ import annotations

import numpy as np

from cvrp.instance import Instance
from cvrp.solution import Solution
from cvrp.timewindows import is_route_tw_feasible


def nearest_neighbor(inst: Instance) -> Solution:
    """Build routes greedily: always drive to the closest customer that still fits.

    A route is closed and a new one opened when no unvisited customer fits in
    the remaining capacity (or, for CVRPTW, cannot be served in its window).
    Complexity O(n^2), each step is one vectorized ``argmin``.
    """
    n = inst.n_customers
    unvisited = np.ones(n + 1, dtype=bool)
    unvisited[0] = False
    routes: list[list[int]] = []

    while unvisited.any():
        route: list[int] = []
        load, current = 0.0, 0
        while True:
            fits = unvisited & (inst.demands + load <= inst.capacity)
            if not fits.any():
                break
            candidates = np.where(fits, inst.dist[current], np.inf)
            nxt = int(np.argmin(candidates))
            if inst.has_time_windows:
                # Try candidates by increasing distance until one keeps the route feasible.
                order = np.argsort(candidates)
                nxt = next(
                    (
                        int(c)
                        for c in order[: int(fits.sum())]
                        if is_route_tw_feasible([*route, int(c)], inst)
                    ),
                    -1,
                )
                if nxt == -1:
                    break
            route.append(nxt)
            unvisited[nxt] = False
            load += inst.demands[nxt]
            current = nxt
        if not route:  # a single customer that cannot be served alone
            raise ValueError("instance is infeasible: a customer cannot be routed")
        routes.append(route)
    return Solution(routes)


def clarke_wright(inst: Instance) -> Solution:
    """Clarke and Wright parallel savings algorithm (1964).

    Start with one route per customer, compute savings
    s_ij = d_0i + d_0j - d_ij, sort them in decreasing order and merge two
    routes whenever i and j are at route ends and the merged load fits.

    TODO(Person 2): implement. Vectorize the savings matrix with numpy
    (``d[0][:, None] + d[0][None, :] - d``) and keep only the upper triangle.
    """
    raise NotImplementedError("Clarke and Wright savings is not implemented yet")


def sweep(inst: Instance) -> Solution:
    """Sweep algorithm (Gillett and Miller, 1974).

    Sort customers by polar angle around the depot and cut the sequence into
    routes whenever capacity would be exceeded; optionally improve each route
    with 2-opt.

    TODO(Person 2): implement with ``np.arctan2`` and a cumulative load cut.
    """
    raise NotImplementedError("sweep is not implemented yet")
