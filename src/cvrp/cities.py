"""Real-city instances from the RRNCO dataset (road network, OpenStreetMap + OSRM).

Source: Son et al., "RRNCO: Towards Real-World Routing with Neural Combinatorial Optimization",
ICLR 2026. Dataset: https://huggingface.co/datasets/ai4co/rrnco
(``dataset/<City>/<City>_data.npz``).

Each city file holds 1,000 real points and two road matrices computed with OSRM:

* ``points``: shape (1000, 2), latitude then longitude;
* ``distance``: shape (1000, 1000), shortest road distance in km;
* ``duration``: shape (1000, 1000), free-flow travel time in minutes.

The matrices are **asymmetric** (one-way streets): ``d[i, j] != d[j, i]``. The files hold no
depot, demands, capacity or time windows, so :func:`load_city` adds them (seeded, reproducible).

Two cost metrics:

* ``metric="distance"``: ``inst.dist`` is the road distance in km (distance objective);
* ``metric="duration"``: ``inst.dist`` is the free-flow time in minutes, which is what the team
  traffic model expects (``tabu.duration_cost`` and GRASP traffic mode multiply ``dist`` by the
  hourly intensity ``RHO`` of notebook 01). The durations are free-flow, so traffic is not
  counted twice.

Example:
    >>> inst = load_city("data/cities/Paris_data.npz", n=1000)      # doctest: +SKIP
    >>> inst.n_customers                                            # doctest: +SKIP
    999
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from cvrp.instance import Instance
from cvrp.utils import make_rng

MAX_NODES = 1000  # points per RRNCO city file (depot included)


def load_city(
    path: str | Path,
    n: int | None = None,
    metric: str = "distance",
    capacity: float = 100.0,
    seed: int | None = 0,
    time_windows: bool = False,
    service_time: float = 5.0,
    day: tuple[float, float] = (480.0, 1080.0),
    window_width: float = 120.0,
    name: str | None = None,
) -> Instance:
    """Build a CVRP (or CVRPTW) instance from one RRNCO city file.

    Args:
        path: Path to ``<City>_data.npz``.
        n: Number of customers; ``None`` (or anything >= 999) keeps all of them. A file has
            1,000 points, so at most 999 customers plus the depot.
        metric: ``"distance"`` (km) or ``"duration"`` (free-flow minutes) as ``inst.dist``.
        capacity: Vehicle capacity Q. Demands are integers in 1..10, as in ``Instance.random``,
            so Q = 100 gives about 18 customers per route.
        seed: Seed for the customer sample, the demands and the time windows.
        time_windows: Add time windows (CVRPTW). Only with ``metric="duration"``, because the
            windows are in minutes after midnight, the convention of the traffic model.
        service_time: Service duration at each customer, in minutes (time windows only).
        day: Depot opening and closing time, minutes after midnight (default 8:00 to 18:00).
        window_width: Width of each customer window, in minutes.
        name: Instance name; ``"<City>-n<n>-<metric>-s<seed>"`` by default.

    Returns:
        The instance; node 0 is the depot, ``coords`` are (longitude, latitude).
    """
    if metric not in ("distance", "duration"):
        raise ValueError(f"metric must be 'distance' or 'duration', not {metric!r}")
    if time_windows and metric != "duration":
        raise ValueError("time windows are in minutes: use metric='duration'")

    data = np.load(Path(path))
    points = np.asarray(data["points"], dtype=float)
    dist_km = np.asarray(data["distance"], dtype=float)
    dur_min = np.asarray(data["duration"], dtype=float)
    full = dist_km if metric == "distance" else dur_min

    rng = make_rng(seed)
    depot = central_node(dist_km)
    others = np.setdiff1d(np.arange(len(points)), [depot])
    if n is None or n >= len(others):
        chosen = others
    else:
        if n < 1:
            raise ValueError("n must be at least 1")
        chosen = np.sort(rng.choice(others, size=n, replace=False))
    nodes = np.concatenate([[depot], chosen])
    k = len(chosen)

    dist = full[np.ix_(nodes, nodes)].copy()
    coords = points[nodes][:, ::-1].copy()  # (lon, lat) so that x = east, y = north
    demands = np.concatenate([[0.0], rng.integers(1, 11, size=k).astype(float)])

    ready = due = service = None
    if time_windows:
        ready, due, service = _time_windows(dist, rng, service_time, day, window_width)

    return Instance(
        name=name or f"{_city_name(path)}-n{k}-{metric}-s{seed}",
        coords=coords,
        demands=demands,
        capacity=float(capacity),
        ready_times=ready,
        due_times=due,
        service_times=service,
        dist=dist,
    )


def central_node(dist: np.ndarray) -> int:
    """Index of the road medoid: the node with the smallest total distance to and from all others.

    The RRNCO files have no depot; a central depot is the usual urban distribution setting.
    """
    return int(np.argmin(dist.sum(axis=0) + dist.sum(axis=1)))


def _time_windows(
    dist: np.ndarray,
    rng: np.random.Generator,
    service_time: float,
    day: tuple[float, float],
    width: float,
    max_rho: float = 1.80,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Random windows of fixed width inside the depot day, each reachable from the depot.

    A window never closes before the truck can arrive leaving at opening time at peak traffic
    (``max_rho`` = the highest hourly intensity of notebook 01), so every customer can be served
    alone and the instance is feasible.
    """
    open_, close = day
    k = len(dist) - 1
    earliest = open_ + max_rho * dist[0, 1:]
    latest_start = close - width - service_time - max_rho * dist[1:, 0]
    start = rng.uniform(open_, np.maximum(open_, latest_start))
    ready = np.concatenate([[open_], start])
    due = np.concatenate([[close], np.maximum(start + width, earliest)])
    service = np.concatenate([[0.0], np.full(k, float(service_time))])
    return ready, due, service


def _city_name(path: str | Path) -> str:
    """``.../92bf-Sao_Paulo_data.npz`` -> ``Sao_Paulo`` (drops a download prefix if any)."""
    parts = re.split(r"[-_]", Path(path).stem.removesuffix("_data"))
    while len(parts) > 1 and any(ch.isdigit() for ch in parts[0]):
        parts.pop(0)
    return "_".join(parts)
