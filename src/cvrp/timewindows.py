"""CVRPTW support: schedules, waiting, feasibility and forward time slack.

Conventions (Solomon): travel time equals distance; a vehicle that arrives
before ``ready_time`` waits; service must start no later than ``due_time``;
the depot window [e_0, l_0] bounds the whole route.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from cvrp.instance import Instance


def route_schedule(route: list[int], inst: Instance) -> dict[str, np.ndarray]:
    """Compute arrival, service start and waiting time along a route.

    The loop is over the nodes of one route only (tens of nodes), so it is
    not a hot spot; numba can compile it if profiling says otherwise.

    Returns:
        Dict with arrays ``arrival``, ``start`` and ``wait`` aligned with
        ``[0, *route, 0]``.
    """
    path = [0, *route, 0]
    e, s, d = inst.ready_times, inst.service_times, inst.dist
    if e is None:
        raise ValueError("instance has no time windows")
    s = np.zeros(len(e)) if s is None else s
    arrival = np.zeros(len(path))
    start = np.zeros(len(path))
    start[0] = e[0]
    for k in range(1, len(path)):
        prev, node = path[k - 1], path[k]
        arrival[k] = start[k - 1] + s[prev] + d[prev, node]
        start[k] = max(arrival[k], e[node])
    return {"arrival": arrival, "start": start, "wait": start - arrival}


def is_route_tw_feasible(route: list[int], inst: Instance) -> bool:
    """Return True when every service starts inside its window, depot included."""
    if not inst.has_time_windows:
        return True
    sched = route_schedule(route, inst)
    path = np.array([0, *route, 0])
    return bool(np.all(sched["start"] <= inst.due_times[path] + 1e-9))


def forward_time_slack(route: list[int], inst: Instance) -> np.ndarray:
    """Return the forward time slack F_k at every position of the route.

    F_k is how much the service start at position k can be postponed without
    breaking any later window (Savelsbergh, 1992). It lets an insertion be
    checked in O(1) instead of re-simulating the route.

    TODO(Person 2): implement with a backward pass over the schedule and use it
    in ``alns.greedy_insertion`` for CVRPTW.
    """
    raise NotImplementedError("forward time slack is not implemented yet")
