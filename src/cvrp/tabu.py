"""Tabu Search for the CVRP and the CVRPTW.

Encoding: a list of routes, each route a list of customers; the depot (node 0) is implicit at
both ends. The objective is a sum of route costs given by ``route_cost(route)``, which returns
``math.inf`` for an infeasible route (capacity or time window). Two route costs are provided:
total distance (Solomon convention, comparable to the best known values) and route duration
with the hourly traffic of notebook 01.

Moves (granular: customer ``c`` is only moved next to one of its ``k_near`` nearest neighbors):
relocate, swap, 2-opt* (exchange the tails of two routes) and 2-opt (reverse a segment).
The route costs, the construction and the moves are independent of the search strategy, so another
algorithm can reuse them and be compared on the same terms.
"""

from __future__ import annotations

import math
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from cvrp.instance import Instance

Routes = list[list[int]]
RouteCost = Callable[[tuple[int, ...]], float]

# Hourly traffic intensity rho_h of notebook 01, section 2 (index = hour of the day).
# fmt: off
RHO = (1.00, 1.00, 1.00, 1.00, 1.00, 1.05, 1.30, 1.75, 1.80, 1.40, 1.20, 1.25,
       1.30, 1.25, 1.20, 1.25, 1.45, 1.80, 1.75, 1.40, 1.10, 1.05, 1.00, 1.00)
# fmt: on


# ----------------------------------------------------------------------------- route costs
LIST_MATRIX_MAX = 3000  # above this many nodes the matrix stays a numpy array (memory)


def _rows(inst: Instance):
    """The matrix as nested lists (fast access) when small, as the numpy array when large.

    Nested lists take about 32 bytes per entry: 3 GB at 10 000 customers, so large instances
    read the array directly (slower access, no copy; a memory mapped matrix stays on disk).
    """
    return inst.dist.tolist() if len(inst.dist) <= LIST_MATRIX_MAX else inst.dist


def distance_cost(inst: Instance) -> RouteCost:
    """Route length, or inf if it breaks capacity or a time window (travel time = distance)."""
    d = _rows(inst)
    q = inst.demands.tolist()
    cap = inst.capacity
    tw = inst.has_time_windows
    e = inst.ready_times.tolist() if tw else None
    l_ = inst.due_times.tolist() if tw else None
    s = inst.service_times.tolist() if inst.service_times is not None else [0.0] * len(q)

    def cost(route: tuple[int, ...]) -> float:
        if sum(q[c] for c in route) > cap:
            return math.inf
        length, t, prev = 0.0, (e[0] if tw else 0.0), 0
        for c in (*route, 0):
            length += d[prev][c]
            if tw:
                t = max(t + s[prev] + d[prev][c], e[c])
                if t > l_[c] + 1e-9:
                    return math.inf
            prev = c
        return length

    return cost


def duration_cost(
    inst: Instance, start_min: float = 480.0, rho: tuple[float, ...] = RHO
) -> RouteCost:
    """Route duration (return minus departure) with the hourly traffic of notebook 01.

    The truck leaves the depot at ``start_min`` (minutes after midnight); a trip leaving at time
    t takes ``rho[hour(t)] * dist``. Waiting before a window and service time are included.
    """
    d = _rows(inst)
    q = inst.demands.tolist()
    cap = inst.capacity
    tw = inst.has_time_windows
    e = inst.ready_times.tolist() if tw else None
    l_ = inst.due_times.tolist() if tw else None
    s = inst.service_times.tolist() if inst.service_times is not None else [0.0] * len(q)

    def cost(route: tuple[int, ...]) -> float:
        if sum(q[c] for c in route) > cap:
            return math.inf
        t, prev = start_min, 0
        for c in route:
            t += rho[int(t // 60) % 24] * d[prev][c]
            if tw:
                t = max(t, e[c])
                if t > l_[c] + 1e-9:
                    return math.inf
            t += s[c]
            prev = c
        t += rho[int(t // 60) % 24] * d[prev][0]
        return t - start_min

    return cost


MEMO_MAX = 1_000_000  # routes kept in the cache; it is emptied when full (memory)


def cached(cost: RouteCost) -> RouteCost:
    """Memoize a route cost: the search revisits the same routes many times.

    The cache is emptied when it holds ``MEMO_MAX`` routes: on 10 000 customers a long run
    evaluates tens of millions of routes and an unbounded cache would fill the memory.
    """
    memo: dict[tuple[int, ...], float] = {(): 0.0}

    def wrapped(route: tuple[int, ...]) -> float:
        v = memo.get(route)
        if v is None:
            if len(memo) >= MEMO_MAX:
                memo.clear()
                memo[()] = 0.0
            v = memo[route] = cost(route)
        return v

    return wrapped


# ----------------------------------------------------------------------------- construction
def nearest_feasible(inst: Instance, cost: RouteCost) -> Routes:
    """Time-oriented nearest neighbor (Solomon, 1987).

    Extend the route with the closest customer that keeps it feasible; open a new route when
    none does.
    """
    alive = np.ones(inst.n_customers + 1, dtype=bool)
    alive[0] = False
    q = inst.demands
    routes: Routes = []
    while alive.any():
        route: list[int] = []
        last, load = 0, 0.0
        while True:
            cand = np.flatnonzero(alive & (q <= inst.capacity - load + 1e-9))
            if not len(cand):
                break
            cand = cand[np.argsort(np.asarray(inst.dist[last])[cand], kind="stable")]
            nxt = next((int(c) for c in cand if math.isfinite(cost((*route, int(c))))), None)
            if nxt is None:
                break
            route.append(nxt)
            alive[nxt] = False
            last, load = nxt, load + q[nxt]
        if not route:
            raise ValueError("a customer cannot be served alone: instance infeasible")
        routes.append(route)
    return routes


# ----------------------------------------------------------------------------- moves
@dataclass
class Move:
    """A candidate move: the routes it rewrites and the customers it touches (tabu)."""

    new: dict[int, list[int]]
    touched: tuple[int, ...]
    delta: float = 0.0


def _where(routes: Routes) -> dict[int, tuple[int, int]]:
    return {c: (r, p) for r, route in enumerate(routes) for p, c in enumerate(route)}


def random_move(
    routes: Routes, pos: dict[int, tuple[int, int]], near: list[list[int]], rng: random.Random
) -> Move | None:
    """Draw one granular move around a random customer and one of its near neighbors."""
    c = rng.randrange(1, len(near))
    v = rng.choice(near[c])
    (rc, pc), (rv, pv) = pos[c], pos[v]
    kind = rng.randrange(4)
    if kind == 0:  # relocate c right after v
        if rc == rv:
            route = routes[rc][:]
            route.pop(pc)
            route.insert(route.index(v) + 1, c)
            return Move({rc: route}, (c,))
        a, b = routes[rc][:], routes[rv][:]
        a.pop(pc)
        b.insert(pv + 1, c)
        return Move({rc: a, rv: b}, (c,))
    if kind == 1:  # swap c and v
        if rc == rv:
            route = routes[rc][:]
            route[pc], route[pv] = route[pv], route[pc]
            return Move({rc: route}, (c, v))
        a, b = routes[rc][:], routes[rv][:]
        a[pc], b[pv] = v, c
        return Move({rc: a, rv: b}, (c, v))
    if kind == 2:  # 2-opt*: route of c keeps its head up to c, then continues with v's tail
        if rc == rv:
            return None
        a, b = routes[rc], routes[rv]
        return Move({rc: a[: pc + 1] + b[pv:], rv: b[:pv] + a[pc + 1 :]}, (c, v))
    if rc != rv:  # 2-opt: reverse the segment between c and v in their common route
        return None
    i, j = sorted((pc, pv))
    route = routes[rc][:]
    route[i : j + 1] = route[i : j + 1][::-1]
    return Move({rc: route}, (c, v))


def _delta(move: Move, routes: Routes, cost: RouteCost) -> float:
    after = sum(cost(tuple(r)) for r in move.new.values())
    return after - sum(cost(tuple(routes[i])) for i in move.new)


def _apply(routes: Routes, move: Move) -> Routes:
    out = [move.new.get(i, r) for i, r in enumerate(routes)]
    return [r for r in out if r]


def neighbor_lists(inst: Instance, k: int) -> list[list[int]]:
    """For every customer, its ``k`` nearest customers (depot excluded).

    Computed by blocks of rows so that a large matrix is never copied whole.
    """
    n = inst.n_customers
    k = min(k, n - 1)
    out: list[list[int]] = [[]]
    for start in range(1, n + 1, 1000):
        rows = np.array(inst.dist[start : start + 1000], dtype=float)
        rows[:, 0] = np.inf
        rows[np.arange(len(rows)), np.arange(start, start + len(rows))] = np.inf
        part = np.argpartition(rows, k - 1, axis=1)[:, :k]
        near = np.take_along_axis(rows, part, axis=1)
        order = np.take_along_axis(part, np.argsort(near, axis=1, kind="stable"), axis=1)
        out += order.tolist()
    return out


# ----------------------------------------------------------------------------- algorithms
@dataclass
class Result:
    """Best solution of a run, its cost, the best cost over time and the work done."""

    routes: Routes
    cost: float
    iterations: int
    seconds: float
    history: list[tuple[float, float]] = field(default_factory=list)  # (seconds, best cost)


@dataclass
class TabuParams:
    """Tabu Search parameters (values chosen by the tuning in experiments/solomon_study.py)."""

    tenure: int = 10  # iterations a moved customer stays tabu
    candidates: int = 200  # granular moves sampled per iteration (candidate list)
    k_near: int = 15  # size of each customer's neighbor list
    time_limit: float = 30.0  # seconds


def tabu_search(
    inst: Instance,
    cost: RouteCost,
    params: TabuParams,
    seed: int = 0,
    initial: Routes | None = None,
) -> Result:
    """Tabu Search: at each iteration apply the best non-tabu move of a sampled candidate list.

    A customer moved at iteration it is tabu (cannot move again) until it + tenure, where the
    tenure is drawn in [tenure / 2, 3 tenure / 2] to avoid cycles. Aspiration: a tabu move is
    allowed if it gives a new best solution. Stops at the time limit.
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)
    cost = cached(cost)
    near = neighbor_lists(inst, params.k_near)
    routes = initial or nearest_feasible(inst, cost)
    cur = sum(cost(tuple(r)) for r in routes)
    best, best_cost = [r[:] for r in routes], cur
    tabu_until: dict[int, int] = {}
    history = [(0.0, best_cost)]
    it = 0
    while time.perf_counter() - t0 < params.time_limit:
        it += 1
        pos = _where(routes)
        chosen: Move | None = None
        for _ in range(params.candidates):
            m = random_move(routes, pos, near, rng)
            if m is None:
                continue
            m.delta = _delta(m, routes, cost)
            if not math.isfinite(m.delta):
                continue
            is_tabu = any(tabu_until.get(c, 0) > it for c in m.touched)
            if is_tabu and cur + m.delta >= best_cost - 1e-9:
                continue
            if chosen is None or m.delta < chosen.delta:
                chosen = m
        if chosen is None:
            continue
        routes = _apply(routes, chosen)
        cur += chosen.delta
        for c in chosen.touched:
            tabu_until[c] = it + rng.randint(params.tenure // 2, 3 * params.tenure // 2)
        if cur < best_cost - 1e-9:
            best, best_cost = [r[:] for r in routes], cur
            history.append((time.perf_counter() - t0, best_cost))
    return Result(best, best_cost, it, time.perf_counter() - t0, history)
