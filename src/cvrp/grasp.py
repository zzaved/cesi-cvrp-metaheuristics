"""GRASP for the CVRP and the CVRPTW (owner: Farida).

Greedy Randomized Adaptive Search Procedure (Feo and Resende, 1995): every
iteration builds one solution with a randomized greedy insertion heuristic and
improves it with a local search; the best feasible solution over all
iterations is returned.

The module only *reads* the shared ``Instance`` and returns a shared
``Solution``, so its output is checked by the same ``Solution.violations``
evaluator as every other algorithm of the team. Nothing in the teammates'
modules is changed.

Design choices, all driven by speed in pure Python:

* Data are copied once into plain Python lists (``_Model``), because indexing
  a list is about ten times faster than indexing a numpy array element by
  element in the inner loops.
* Each route caches its service start times ``A`` (forward pass) and its
  latest feasible start times ``Z`` (backward pass, Savelsbergh 1992). With
  them, the time-window feasibility of relocate, swap, Or-opt and 2-opt*
  moves is checked in O(1) (plus the length of the moved segment) instead of
  re-simulating the route.
* The local search is *granular* (Toth and Vigo, 2003): a move is only tried
  between a customer and its ``n_neighbors`` closest customers.

Construction (randomized, adaptive):
    Parallel cheapest insertion. For every unrouted customer, the cheapest
    feasible insertion over all open routes is kept up to date (only the
    route that changed is re-evaluated). The restricted candidate list (RCL)
    holds the customers whose score is within ``alpha`` of the best one:
    ``score <= s_min + alpha * (s_max - s_min)``. One of them is drawn at
    random and inserted. With ``construction="regret"`` the score is the
    insertion cost minus the regret (second best route minus best route), so
    customers with few good options are served first. When no customer fits
    anywhere a new route is opened with a seed customer (far from the depot
    or with an early due date).

Local search (Variable Neighborhood Descent):
    relocate -> swap -> 2-opt* -> Or-opt (2-3 customers) -> intra 2-opt, and
    with ``enhanced=True`` also cross-exchange of segments of up to 2
    customers. After an improvement the descent restarts from the first
    neighborhood. ``improvement="first"`` applies the first improving move
    found, ``"best"`` scans the whole neighborhood and applies the best one.

Optional extension (``perturb_kicks > 0``):
    after the descent, a few kick-and-descend rounds (remove 10-20 % of the
    customers around a random seed and reinsert them greedily, then descend
    again; keep the result only if it is better). This turns each GRASP
    iteration into a short iterated local search, a classical GRASP
    hybridization (Resende and Ribeiro, 2010, "GRASP with ILS"). It is off by
    default, so the plain GRASP can be reported separately.
"""

# Names follow the math of the docstrings (D = distances, A/Z = start times, l = due times).
# ruff: noqa: N806, E741

from __future__ import annotations

import math
import random
import time
from array import array
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from cvrp.instance import Instance
from cvrp.solution import Solution
from cvrp.tabu import cached, duration_cost

EPS = 1e-7
INF = float("inf")


# --------------------------------------------------------------------------- #
# Parameters and result                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class GRASPParams:
    """Parameters of the GRASP. Defaults are the tuned values (see notebook 04).

    Attributes:
        alpha: RCL greediness, 0 = pure greedy, 1 = pure random.
        iterations: Number of construct + local search iterations.
        improvement: ``"first"`` or ``"best"`` improvement in the local search.
        enhanced: Add cross-exchange (segments of up to 2 customers).
        max_local_rounds: Upper bound on improving moves per local search.
        n_neighbors: Size of the granular neighbor list of each customer.
        construction: ``"cheapest"`` or ``"regret"`` insertion score.
        tw_weight: Weight of the time push-forward in the insertion score
            (Solomon I1 idea); 0 means pure distance.
        perturb_kicks: Kick-and-descend rounds after each descent (0 = plain GRASP).
        time_limit: Optional wall-clock limit in seconds, checked between
            iterations and between kicks (the current descent always finishes;
            in traffic mode it is also checked inside the descent).
        objective: ``"distance"`` (total distance, travel time = distance, used
            for the Solomon benchmark) or ``"duration"`` (total route duration
            with hourly traffic, the team model of notebook 01).
        start_min: Depot departure in minutes after midnight (traffic mode only).
        local_search: ``"vnd"`` (full VND passes over all customers, the setting of the
            Solomon campaign) or ``"dlb"`` (localized descent with don't-look bits: after a
            kick only the modified routes are re-examined, and the time limit is also checked
            inside the descent). ``"dlb"`` is the large-instance setting (Homberger, cities,
            10,000 customers).
        kick_size: Fraction range of customers removed by one kick (distance mode).
        kick_max: Upper bound on the customers removed by one kick (``None`` = no bound),
            so that kicks stay local on large instances.
        construction: also accepts ``"nearest"``: randomized nearest-neighbor route building
            over the granular neighbor lists, O(n k), for instances too large for the
            O(n^2) insertion heuristics (10,000 customers).
    """

    alpha: float = 0.1
    iterations: int = 30
    improvement: str = "first"
    enhanced: bool = True
    max_local_rounds: int = 100_000
    n_neighbors: int = 20
    construction: str = "regret"
    tw_weight: float = 0.0
    perturb_kicks: int = 0
    time_limit: float | None = None
    objective: str = "distance"
    start_min: float = 480.0
    local_search: str = "vnd"
    kick_size: tuple[float, float] = (0.10, 0.20)
    kick_max: int | None = None


@dataclass
class GRASPResult:
    """Output of :func:`grasp`.

    Attributes:
        best: Best feasible solution found (``None`` if none was feasible).
        cost: Its total distance, or its total duration in minutes in traffic
            mode (``inf`` if none).
        runtime: Wall-clock seconds.
        iterations: Iterations actually performed.
        history: One dict per iteration: constructed cost, cost after local
            search, best so far, number of routes, feasibility, seconds.
    """

    best: Solution | None
    cost: float
    runtime: float
    iterations: int
    history: list[dict] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Instance data as plain lists                                                 #
# --------------------------------------------------------------------------- #
class _Model:
    """Read-only copy of the instance in Python lists, plus neighbor lists."""

    def __init__(self, inst: Instance, n_neighbors: int) -> None:
        n = inst.n_customers
        self.n = n
        if n <= 2000:
            self.D = inst.dist.tolist()
        else:
            # Large n: one typed array per row (8 bytes per entry instead of about 32 for
            # a list of Python floats): 0.8 GB instead of 3.2 GB at 10,000 customers.
            self.D = [array("d", row) for row in inst.dist]
        self.dem = inst.demands.tolist()
        self.Q = float(inst.capacity)
        self.K = inst.num_vehicles if inst.num_vehicles is not None else n
        self.tw = inst.has_time_windows
        if self.tw:
            self.e = inst.ready_times.tolist()
            self.l = inst.due_times.tolist()
            st = inst.service_times
            self.s = [0.0] * (n + 1) if st is None else st.tolist()
        else:
            self.e = [0.0] * (n + 1)
            self.l = [INF] * (n + 1)
            self.s = [0.0] * (n + 1)
        # k nearest customers of each customer (depot excluded), by distance.
        k = min(n_neighbors, n - 1)
        if n <= 2000:
            order = np.argsort(inst.dist[1:, 1:], axis=1)[:, 1 : k + 1] + 1
            self.neigh = [[]] + [row.tolist() for row in order]
        else:
            # Large n: partial sort per block of rows (O(n^2) instead of O(n^2 log n),
            # and no n x n index matrix in memory).
            self.neigh = [[]]
            for lo in range(1, n + 1, 1000):
                block = inst.dist[lo : min(n + 1, lo + 1000), 1:].copy()
                block[np.arange(len(block)), np.arange(lo - 1, lo - 1 + len(block))] = np.inf
                part = np.argpartition(block, k, axis=1)[:, :k]
                vals = np.take_along_axis(block, part, axis=1)
                part = np.take_along_axis(part, np.argsort(vals, axis=1), axis=1) + 1
                self.neigh += [row.tolist() for row in part]


# --------------------------------------------------------------------------- #
# Route state: cached loads, times and latest times                            #
# --------------------------------------------------------------------------- #
class _Route:
    """One route with depot sentinels, ``path = [0, c1, ..., cm, 0]``.

    Cached arrays, aligned with ``path``:
        A[k]: service start at position k (earliest, with waiting).
        Z[k]: latest service start at position k such that the rest of the
              route stays feasible (backward pass).
        L[k]: cumulative load up to and including position k.
    """

    __slots__ = ("path", "A", "Z", "L", "load", "cost")

    def __init__(self, customers: list[int], m: _Model) -> None:
        self.path = [0, *customers, 0]
        self.update(m)

    def update(self, m: _Model) -> None:
        """Recompute every cached value in O(route length)."""
        p, D, e, l, s, dem = self.path, m.D, m.e, m.l, m.s, m.dem
        size = len(p)
        A = [0.0] * size
        L = [0.0] * size
        A[0] = e[0]
        cost = 0.0
        for k in range(1, size):
            a, b = p[k - 1], p[k]
            dab = D[a][b]
            cost += dab
            t = A[k - 1] + s[a] + dab
            A[k] = t if t > e[b] else e[b]
            L[k] = L[k - 1] + dem[b]
        Z = [0.0] * size
        Z[-1] = l[0]
        for k in range(size - 2, -1, -1):
            a, b = p[k], p[k + 1]
            t = Z[k + 1] - s[a] - D[a][b]
            Z[k] = t if t < l[a] else l[a]
        self.A, self.Z, self.L = A, Z, L
        self.load = L[-1]
        self.cost = cost

    def customers(self) -> list[int]:
        """Return the customers without the depot sentinels."""
        return self.path[1:-1]


def _seq_ok(m: _Model, t: float, prev: int, seq: list[int] | tuple, nxt: int, znxt: float) -> bool:
    """Check a route piece in O(len(seq)).

    The vehicle starts serving ``prev`` at time ``t``, then visits ``seq`` in
    order, then reaches ``nxt``, whose latest feasible start is ``znxt``.
    """
    D, e, l, s = m.D, m.e, m.l, m.s
    cur = prev
    for u in seq:
        t = t + s[cur] + D[cur][u]
        if t < e[u]:
            t = e[u]
        if t > l[u] + EPS:
            return False
        cur = u
    return t + s[cur] + D[cur][nxt] <= znxt + EPS


def _route_ok(m: _Model, customers: list[int]) -> tuple[bool, float, float]:
    """Full check of a candidate route: (time windows ok, load, cost)."""
    D, e, l, s, dem = m.D, m.e, m.l, m.s, m.dem
    t, cur, load, cost = e[0], 0, 0.0, 0.0
    for u in customers:
        cost += D[cur][u]
        t = t + s[cur] + D[cur][u]
        if t < e[u]:
            t = e[u]
        if t > l[u] + EPS:
            return False, load, cost
        load += dem[u]
        cur = u
    cost += D[cur][0]
    return t + s[cur] + D[cur][0] <= l[0] + EPS, load, cost


# --------------------------------------------------------------------------- #
# Solution state used by construction and local search                         #
# --------------------------------------------------------------------------- #
class _State:
    """Routes plus the position index ``where[u] = (route index, position)``."""

    def __init__(self, m: _Model, routes: list[list[int]] | None = None) -> None:
        self.m = m
        self.routes: list[_Route] = [_Route(r, m) for r in (routes or []) if r]
        self.where: list[tuple[int, int]] = [(-1, -1)] * (m.n + 1)
        self.reindex_all()

    def reindex_all(self) -> None:
        """Rebuild the position index of every route."""
        for ri in range(len(self.routes)):
            self.reindex(ri)

    def reindex(self, ri: int) -> None:
        """Rebuild the position index of route ``ri``."""
        w = self.where
        for k, u in enumerate(self.routes[ri].path[1:-1], start=1):
            w[u] = (ri, k)

    def set_route(self, ri: int, customers: list[int]) -> None:
        """Replace the customers of route ``ri`` and refresh its caches."""
        r = self.routes[ri]
        r.path = [0, *customers, 0]
        r.update(self.m)
        self.reindex(ri)

    def drop_empty(self) -> None:
        """Remove empty routes and rebuild the index if anything changed."""
        if any(len(r.path) == 2 for r in self.routes):
            self.routes = [r for r in self.routes if len(r.path) > 2]
            self.reindex_all()

    def cost(self) -> float:
        """Total distance."""
        return sum(r.cost for r in self.routes)

    def to_solution(self) -> Solution:
        """Export as the shared ``Solution`` class."""
        return Solution([r.customers() for r in self.routes if len(r.path) > 2])


# --------------------------------------------------------------------------- #
# Construction: randomized adaptive insertion                                  #
# --------------------------------------------------------------------------- #
def _best_insertion(m: _Model, r: _Route, u: int, tw_weight: float) -> tuple[float, int]:
    """Cheapest feasible position to insert ``u`` in route ``r``: (score, position)."""
    if r.load + m.dem[u] > m.Q + EPS:
        return INF, -1
    D, p, A, Z, s, e = m.D, r.path, r.A, r.Z, m.s, m.e
    best, best_k = INF, -1
    Du = D[u]
    for k in range(len(p) - 1):
        a, b = p[k], p[k + 1]
        c = D[a][u] + Du[b] - D[a][b]
        if c >= best:
            continue
        if m.tw:
            t = A[k] + s[a] + D[a][u]
            if t < e[u]:
                t = e[u]
            if t > m.l[u] + EPS:
                continue
            arr_b = t + s[u] + Du[b]
            if arr_b > Z[k + 1] + EPS:
                continue
            if tw_weight:
                new_b = arr_b if arr_b > e[b] else e[b]
                c += tw_weight * (new_b - A[k + 1])
        if c < best:
            best, best_k = c, k
    return best, best_k


def construct(m: _Model, rng: random.Random, alpha: float, mode: str, tw_weight: float) -> _State:
    """Randomized parallel insertion (the "greedy randomized" phase of GRASP).

    Args:
        m: Instance data.
        rng: Random generator (seeded by the caller for reproducibility).
        alpha: RCL threshold in [0, 1].
        mode: ``"cheapest"`` or ``"regret"`` score.
        tw_weight: Weight of the time push-forward term in the insertion cost.

    Returns:
        A state where every customer is routed (the fleet limit may be exceeded
        if the instance is very tight; the caller checks it).
    """
    st = _State(m)
    unrouted = set(range(1, m.n + 1))
    # cand[u][ri] = (score, position) of the best insertion of u in route ri.
    cand: dict[int, list[tuple[float, int]]] = {u: [] for u in unrouted}

    def open_route() -> None:
        # Seed: random pick among the farthest / earliest-due unrouted customers.
        pool = sorted(unrouted, key=lambda c: (-m.D[0][c], m.l[c]))
        if m.tw and rng.random() < 0.5:
            pool = sorted(unrouted, key=lambda c: m.l[c])
        top = pool[: max(1, int(math.ceil(alpha * len(pool) * 0.2)) + 1)]
        u = rng.choice(top)
        st.routes.append(_Route([u], m))
        unrouted.discard(u)
        cand.pop(u, None)
        ri = len(st.routes) - 1
        st.reindex(ri)
        r = st.routes[ri]
        for v in unrouted:
            cand[v].append(_best_insertion(m, r, v, tw_weight))

    open_route()
    while unrouted:
        scores: list[tuple[float, int]] = []
        for u in unrouted:
            opts = cand[u]
            b1 = b2 = INF
            for sc, _ in opts:
                if sc < b1:
                    b1, b2 = sc, b1
                elif sc < b2:
                    b2 = sc
            if b1 == INF:
                continue
            if mode == "regret":
                reg = (b2 - b1) if b2 < INF else 2.0 * m.D[0][u]
                scores.append((b1 - reg, u))
            else:
                scores.append((b1, u))
        if not scores:
            open_route()
            continue
        lo = min(sc for sc, _ in scores)
        hi = max(sc for sc, _ in scores)
        thr = lo + alpha * (hi - lo) + EPS
        rcl = [u for sc, u in scores if sc <= thr]
        u = rng.choice(rcl)
        opts = cand.pop(u)
        ri = min(range(len(opts)), key=lambda i: opts[i][0])
        pos = opts[ri][1]
        r = st.routes[ri]
        r.path.insert(pos + 1, u)
        r.update(m)
        st.reindex(ri)
        unrouted.discard(u)
        for v in unrouted:  # adaptive part: only the modified route is re-evaluated
            cand[v][ri] = _best_insertion(m, r, v, tw_weight)
    return st


def construct_nearest(m: _Model, rng: random.Random, alpha: float) -> _State:
    """Randomized nearest-neighbor construction, O(n k) (large instances).

    Each route starts at a random customer among the farthest unrouted ones, then
    repeatedly appends a customer drawn from an RCL of the feasible unrouted neighbors of
    the last customer (cost within ``alpha`` of the cheapest). When no neighbor fits, the
    route is closed. The neighbor lists replace the O(n) scan of the insertion heuristics,
    so 10,000 customers are built in about a second.
    """
    D, dem, Q, e, l, s = m.D, m.dem, m.Q, m.e, m.l, m.s
    unrouted = bytearray([0] + [1] * m.n)
    left = m.n
    by_far = sorted(range(1, m.n + 1), key=lambda c: -D[0][c])
    far_ptr = 0
    routes: list[list[int]] = []
    while left:
        while not unrouted[by_far[far_ptr]]:
            far_ptr += 1
        pool = [c for c in by_far[far_ptr : far_ptr + 50] if unrouted[c]]
        u = rng.choice(pool[: max(1, int(alpha * len(pool)) + 1)])
        route, load = [u], dem[u]
        t = max(e[u], e[0] + D[0][u])
        unrouted[u] = 0
        left -= 1
        while True:
            last = route[-1]
            cands = []
            for v in m.neigh[last]:
                if not unrouted[v] or load + dem[v] > Q + EPS:
                    continue
                if m.tw:
                    tv = max(e[v], t + s[last] + D[last][v])
                    if tv > l[v] + EPS or tv + s[v] + D[v][0] > l[0] + EPS:
                        continue
                cands.append((D[last][v], v))
            if not cands and load < 0.9 * Q:
                # All neighbors are used: fall back to the nearest feasible unrouted customer.
                Dl = D[last]
                for v in range(1, m.n + 1):
                    if not unrouted[v] or load + dem[v] > Q + EPS:
                        continue
                    if m.tw:
                        tv = max(e[v], t + s[last] + Dl[v])
                        if tv > l[v] + EPS or tv + s[v] + D[v][0] > l[0] + EPS:
                            continue
                    if not cands or Dl[v] < cands[0][0]:
                        cands = [(Dl[v], v)]
            if not cands:
                break
            lo = min(c for c, _ in cands)
            hi = max(c for c, _ in cands)
            v = rng.choice([v for c, v in cands if c <= lo + alpha * (hi - lo) + EPS])
            if m.tw:
                t = max(e[v], t + s[last] + D[last][v])
            route.append(v)
            load += dem[v]
            unrouted[v] = 0
            left -= 1
        routes.append(route)
    return _State(m, routes)


# --------------------------------------------------------------------------- #
# Local search                                                                 #
# --------------------------------------------------------------------------- #
class _LocalSearch:
    """Granular VND over relocate, swap, 2-opt*, Or-opt, 2-opt and cross-exchange.

    Each ``_scan_*`` method yields improving feasible moves for customer ``u``
    as tuples ``(delta, kind, args)``; ``_apply`` performs a move.
    """

    def __init__(self, m: _Model, st: _State, rng: random.Random, p: GRASPParams) -> None:
        self.m, self.st, self.rng, self.p = m, st, rng, p
        ops = [self._scan_relocate, self._scan_swap, self._scan_two_opt_star, self._scan_or_opt]
        if p.enhanced:
            ops.append(self._scan_cross)
        ops.append(self._scan_two_opt)
        self.ops = ops

    # ---------- driver ---------- #
    def run(self) -> int:
        """Run the descent until no neighborhood improves; return the number of moves."""
        moves, k = 0, 0
        order = list(range(1, self.m.n + 1))
        first = self.p.improvement == "first"
        while k < len(self.ops) and moves < self.p.max_local_rounds:
            op = self.ops[k]
            self.rng.shuffle(order)
            improved = False
            if first:
                for u in order:
                    for mv in op(u):
                        self._apply(mv)
                        moves += 1
                        improved = True
                        break
            else:
                best = None
                for u in order:
                    for mv in op(u):
                        if best is None or mv[0] < best[0]:
                            best = mv
                if best is not None:
                    self._apply(best)
                    moves += 1
                    improved = True
            k = 0 if improved else k + 1
        return moves

    # ---------- relocate one customer ---------- #
    def _scan_relocate(self, u: int):
        m, st = self.m, self.st
        D = m.D
        ru, pu = st.where[u]
        R = st.routes[ru]
        p = R.path
        a, b = p[pu - 1], p[pu + 1]
        gain = D[a][u] + D[u][b] - D[a][b]
        if gain <= EPS:
            return
        rem_ok = (not m.tw) or _seq_ok(m, R.A[pu - 1], a, (), b, R.Z[pu + 1])
        for v in m.neigh[u]:
            rv, pv = st.where[v]
            T = st.routes[rv]
            q = T.path
            if rv == ru:
                for k in (pv - 1, pv):  # insert between q[k] and q[k+1]
                    if k == pu - 1 or k == pu:
                        continue
                    x, y = q[k], q[k + 1]
                    delta = D[x][u] + D[u][y] - D[x][y] - gain
                    if delta >= -EPS:
                        continue
                    cust = p[1:-1]
                    cust.remove(u)
                    ins = k if k < pu else k - 1
                    cust.insert(ins, u)
                    if m.tw and not _route_ok(m, cust)[0]:
                        continue
                    yield (delta, "route1", (ru, cust))
                continue
            if not rem_ok or T.load + m.dem[u] > m.Q + EPS:
                continue
            for k in (pv - 1, pv):
                x, y = q[k], q[k + 1]
                delta = D[x][u] + D[u][y] - D[x][y] - gain
                if delta >= -EPS:
                    continue
                if m.tw and not _seq_ok(m, T.A[k], x, (u,), y, T.Z[k + 1]):
                    continue
                new_u = p[1:pu] + p[pu + 1 : -1]
                new_v = q[1 : k + 1] + [u] + q[k + 1 : -1]
                yield (delta, "route2", (ru, new_u, rv, new_v))

    # ---------- swap two customers of different routes ---------- #
    def _scan_swap(self, u: int):
        m, st = self.m, self.st
        D = m.D
        ru, pu = st.where[u]
        R = st.routes[ru]
        p = R.path
        a, b = p[pu - 1], p[pu + 1]
        for v in m.neigh[u]:
            rv, pv = st.where[v]
            if rv == ru:
                continue
            T = st.routes[rv]
            q = T.path
            x, y = q[pv - 1], q[pv + 1]
            delta = (D[a][v] + D[v][b] - D[a][u] - D[u][b]) + (
                D[x][u] + D[u][y] - D[x][v] - D[v][y]
            )
            if delta >= -EPS:
                continue
            du, dv = m.dem[u], m.dem[v]
            if R.load - du + dv > m.Q + EPS or T.load - dv + du > m.Q + EPS:
                continue
            if m.tw and not (
                _seq_ok(m, R.A[pu - 1], a, (v,), b, R.Z[pu + 1])
                and _seq_ok(m, T.A[pv - 1], x, (u,), y, T.Z[pv + 1])
            ):
                continue
            new_u = p[1:pu] + [v] + p[pu + 1 : -1]
            new_v = q[1:pv] + [u] + q[pv + 1 : -1]
            yield (delta, "route2", (ru, new_u, rv, new_v))

    # ---------- 2-opt*: exchange route tails, creating edge (u, v) ---------- #
    def _scan_two_opt_star(self, u: int):
        m, st = self.m, self.st
        D, Q = m.D, m.Q
        ru, i = st.where[u]
        R = st.routes[ru]
        p = R.path
        un = p[i + 1]
        for v in m.neigh[u]:
            rv, j = st.where[v]
            if rv == ru:
                continue
            T = st.routes[rv]
            q = T.path
            vp = q[j - 1]
            # r1' = p[0..i] + q[j..]   r2' = q[0..j-1] + p[i+1..]
            delta = D[u][v] + D[vp][un] - D[u][un] - D[vp][v]
            if delta >= -EPS:
                continue
            if R.L[i] + (T.load - T.L[j - 1]) > Q + EPS:
                continue
            if T.L[j - 1] + (R.load - R.L[i]) > Q + EPS:
                continue
            if m.tw and not (
                R.A[i] + m.s[u] + D[u][v] <= T.Z[j] + EPS
                and T.A[j - 1] + m.s[vp] + D[vp][un] <= R.Z[i + 1] + EPS
            ):
                continue
            new_u = p[1 : i + 1] + q[j:-1]
            new_v = q[1:j] + p[i + 1 : -1]
            yield (delta, "route2", (ru, new_u, rv, new_v))

    # ---------- Or-opt: move a chain of 2 or 3 customers starting at u ---------- #
    def _scan_or_opt(self, u: int):
        m, st = self.m, self.st
        D = m.D
        ru, pu = st.where[u]
        R = st.routes[ru]
        p = R.path
        for ln in (2, 3):
            end = pu + ln - 1
            if end > len(p) - 2:
                break
            seg = p[pu : end + 1]
            a, b = p[pu - 1], p[end + 1]
            f, g = seg[0], seg[-1]
            gain = D[a][f] + D[g][b] - D[a][b]
            if gain <= EPS:
                continue
            seg_load = R.L[end] - R.L[pu - 1]
            rem_ok = (not m.tw) or _seq_ok(m, R.A[pu - 1], a, (), b, R.Z[end + 1])
            for v in m.neigh[g]:  # put the chain right before v (edge g -> v)
                rv, pv = st.where[v]
                if rv == ru:
                    continue
                T = st.routes[rv]
                q = T.path
                if not rem_ok or T.load + seg_load > m.Q + EPS:
                    continue
                x = q[pv - 1]
                delta = D[x][f] + D[g][v] - D[x][v] - gain
                if delta >= -EPS:
                    continue
                if m.tw and not _seq_ok(m, T.A[pv - 1], x, seg, v, T.Z[pv]):
                    continue
                new_u = p[1:pu] + p[end + 1 : -1]
                new_v = q[1:pv] + seg + q[pv:-1]
                yield (delta, "route2", (ru, new_u, rv, new_v))

    # ---------- cross-exchange of segments of length 1-2 (enhanced) ---------- #
    def _scan_cross(self, u: int):
        m, st = self.m, self.st
        D = m.D
        ru, pu = st.where[u]
        R = st.routes[ru]
        p = R.path
        for v in m.neigh[u]:
            rv, pv = st.where[v]
            if rv == ru:
                continue
            T = st.routes[rv]
            q = T.path
            for la in (1, 2):
                ea = pu + la - 1
                if ea > len(p) - 2:
                    break
                for lb in (1, 2):
                    if la == 1 and lb == 1:
                        continue  # that is a plain swap
                    eb = pv + lb - 1
                    if eb > len(q) - 2:
                        break
                    sa, sb = p[pu : ea + 1], q[pv : eb + 1]
                    a, b = p[pu - 1], p[ea + 1]
                    x, y = q[pv - 1], q[eb + 1]
                    delta = (D[a][sb[0]] + D[sb[-1]][b] - D[a][sa[0]] - D[sa[-1]][b]) + (
                        D[x][sa[0]] + D[sa[-1]][y] - D[x][sb[0]] - D[sb[-1]][y]
                    )
                    if delta >= -EPS:
                        continue
                    la_load = R.L[ea] - R.L[pu - 1]
                    lb_load = T.L[eb] - T.L[pv - 1]
                    if R.load - la_load + lb_load > m.Q + EPS:
                        continue
                    if T.load - lb_load + la_load > m.Q + EPS:
                        continue
                    if m.tw and not (
                        _seq_ok(m, R.A[pu - 1], a, sb, b, R.Z[ea + 1])
                        and _seq_ok(m, T.A[pv - 1], x, sa, y, T.Z[eb + 1])
                    ):
                        continue
                    new_u = p[1:pu] + sb + p[ea + 1 : -1]
                    new_v = q[1:pv] + sa + q[eb + 1 : -1]
                    yield (delta, "route2", (ru, new_u, rv, new_v))

    # ---------- intra-route 2-opt (segment reversal) ---------- #
    def _scan_two_opt(self, u: int):
        m, st = self.m, self.st
        D = m.D
        ru, i = st.where[u]
        p = st.routes[ru].path
        # Reverse p[i+1..j]: edges (u, p[i+1]), (p[j], p[j+1]) become (u, p[j]), (p[i+1], p[j+1]).
        un = p[i + 1]
        # Asymmetric matrices (real road networks): reversing the segment also reverses its
        # inner arcs, so add (backward - forward) length of p[i+1..j], kept as running sums.
        fwd = bwd = 0.0
        for j in range(i + 2, len(p) - 1):
            w, wn = p[j], p[j + 1]
            fwd += D[p[j - 1]][w]
            bwd += D[w][p[j - 1]]
            delta = D[u][w] + D[un][wn] - D[u][un] - D[w][wn] + bwd - fwd
            if delta >= -EPS:
                continue
            cust = p[1 : i + 1] + p[i + 1 : j + 1][::-1] + p[j + 1 : -1]
            if m.tw and not _route_ok(m, cust)[0]:
                continue
            yield (delta, "route1", (ru, cust))

    # ---------- apply ---------- #
    def _apply(self, mv) -> list[int]:
        """Perform a move; return the customers of the routes it changed."""
        _, kind, args = mv
        st = self.st
        if kind == "route1":
            ri, cust = args
            st.set_route(ri, cust)
            touched = list(cust)
        else:
            ra, ca, rb, cb = args
            st.set_route(ra, ca)
            st.set_route(rb, cb)
            touched = ca + cb
        st.drop_empty()
        return touched

    # ---------- localized descent (don't-look bits) ---------- #
    def run_local(self, active=None, deadline: float | None = None) -> int:
        """Descent restricted to "active" customers (Bentley's don't-look bits).

        A queue holds the customers worth re-examining. For the popped customer every
        neighborhood is tried in VND order; after an improving move the customers of the
        changed routes go back into the queue, otherwise the customer is dropped. Starting
        from all customers this is a full descent; after a kick only the customers of the
        modified routes are re-examined, which keeps one kick cheap on large instances.
        """
        n = self.m.n
        start = list(range(1, n + 1)) if active is None else [u for u in active if u]
        self.rng.shuffle(start)
        queue = deque(start)
        inq = bytearray(n + 1)
        for u in start:
            inq[u] = 1
        first = self.p.improvement == "first"
        moves = pops = 0
        while queue and moves < self.p.max_local_rounds:
            pops += 1
            if deadline is not None and pops % 256 == 0 and time.perf_counter() > deadline:
                break
            u = queue.popleft()
            inq[u] = 0
            for op in self.ops:
                if first:
                    mv = next(op(u), None)
                else:
                    mv = min(op(u), key=lambda x: x[0], default=None)
                if mv is None:
                    continue
                touched = self._apply(mv)
                moves += 1
                for v in touched:
                    if not inq[v]:
                        inq[v] = 1
                        queue.append(v)
                break
        return moves


# --------------------------------------------------------------------------- #
# Repair helpers: route elimination and kick (destroy and repair)              #
# --------------------------------------------------------------------------- #
def _reinsert(m: _Model, st: _State, customers: list[int], rng: random.Random) -> bool:
    """Insert customers one by one at their cheapest feasible position.

    Customers that fit nowhere get a new route if the fleet allows it.
    Returns False only when a customer cannot be placed at all.
    """
    rng.shuffle(customers)
    customers.sort(key=lambda c: m.l[c] - m.e[c])  # tight windows first
    for u in customers:
        best, best_ri, best_k = INF, -1, -1
        for ri, r in enumerate(st.routes):
            c, k = _best_insertion(m, r, u, 0.0)
            if c < best:
                best, best_ri, best_k = c, ri, k
        if best_ri < 0:
            if len(st.routes) >= m.K:
                return False
            st.routes.append(_Route([u], m))
            st.reindex(len(st.routes) - 1)
            continue
        r = st.routes[best_ri]
        r.path.insert(best_k + 1, u)
        r.update(m)
        st.reindex(best_ri)
    return True


def _eliminate_routes(m: _Model, st: _State, rng: random.Random) -> None:
    """Try to empty the smallest routes while the fleet limit is exceeded."""
    tries = 0
    while len(st.routes) > m.K and tries < 3 * len(st.routes):
        tries += 1
        ri = min(range(len(st.routes)), key=lambda i: len(st.routes[i].path))
        removed = st.routes.pop(ri).customers()
        st.reindex_all()
        backup = [r.customers() for r in st.routes]
        if not _reinsert(m, st, removed, rng):
            st.routes = [_Route(c, m) for c in backup] + [_Route(removed, m)]
            st.reindex_all()
            break


def _kick(
    m: _Model,
    st: _State,
    rng: random.Random,
    size: tuple[float, float] = (0.10, 0.20),
    kmax: int | None = None,
) -> tuple[_State, set[int]]:
    """Remove a cluster of customers (``size`` fraction, at most ``kmax``) and reinsert them.

    Returns the new state and the customers of every route the kick changed (all of them
    if the kick failed and the old state is returned unchanged, so nothing is skipped).
    """
    k = max(3, int(rng.uniform(*size) * m.n))
    if kmax is not None:
        k = max(3, min(k, kmax))
    seed = rng.randint(1, m.n)
    # Cluster = the seed plus its neighbors, grown through neighbors of neighbors if needed.
    removed = [seed]
    seen = {seed}
    head = 0
    while len(removed) < k and head < len(removed):
        for v in m.neigh[removed[head]]:
            if v not in seen:
                seen.add(v)
                removed.append(v)
                if len(removed) >= k:
                    break
        head += 1
    if len(removed) < k:
        removed += [c for c in rng.sample(range(1, m.n + 1), min(m.n, 2 * k)) if c not in seen]
        removed = removed[:k]
    rem = set(removed)
    before = {tuple(r.path) for r in st.routes}
    new = _State(m, [[c for c in r.customers() if c not in rem] for r in st.routes])
    if not _reinsert(m, new, removed, rng):
        return st, set()
    touched: set[int] = set()
    for r in new.routes:
        if tuple(r.path) not in before:
            touched.update(r.path[1:-1])
    return new, touched


# --------------------------------------------------------------------------- #
# Main loop                                                                    #
# --------------------------------------------------------------------------- #
def grasp(
    inst: Instance,
    params: GRASPParams | None = None,
    seed: int | None = 0,
    verbose: bool = False,
    model: _Model | None = None,
) -> GRASPResult:
    """Run the GRASP and return the best feasible solution found.

    Args:
        inst: Shared ``Instance`` (CVRP or CVRPTW). Its ``dist`` matrix is the
            objective, so set the rounding convention before calling.
        params: Parameters; defaults to ``GRASPParams()``.
        seed: Seed of the random generator (same seed, same result).
        verbose: Print one line per iteration.
        model: Prebuilt ``_Model(inst, params.n_neighbors)`` to reuse between runs on the
            same (large) instance; built here when ``None``.

    Returns:
        A :class:`GRASPResult`. Feasibility is checked with the shared
        ``Solution.violations`` evaluator, not with the internal caches.
    """
    p = params or GRASPParams()
    if p.objective == "duration":
        return _grasp_traffic(inst, p, seed, verbose)
    if p.objective != "distance":
        raise ValueError(f"unknown objective {p.objective!r}")
    rng = random.Random(seed)
    m = model if model is not None else _Model(inst, p.n_neighbors)
    t0 = time.perf_counter()
    best_sol, best_cost = None, INF
    history: list[dict] = []
    it = 0
    if p.local_search not in ("vnd", "dlb"):
        raise ValueError(f"unknown local_search {p.local_search!r}")
    dlb = p.local_search == "dlb"
    deadline = None if p.time_limit is None else t0 + p.time_limit
    kicks_done = 0
    for it in range(1, p.iterations + 1):
        if p.construction == "nearest":
            st = construct_nearest(m, rng, p.alpha)
        else:
            st = construct(m, rng, p.alpha, p.construction, p.tw_weight)
        c_constr = st.cost()
        if len(st.routes) > m.K:
            _eliminate_routes(m, st, rng)
        if dlb:
            _LocalSearch(m, st, rng, p).run_local(None, deadline)
        else:
            _LocalSearch(m, st, rng, p).run()
        for _ in range(p.perturb_kicks):
            if p.time_limit is not None and time.perf_counter() - t0 > p.time_limit:
                break
            cand, touched = _kick(m, st, rng, p.kick_size, p.kick_max)
            if dlb:
                _LocalSearch(m, cand, rng, p).run_local(touched, deadline)
            else:
                _LocalSearch(m, cand, rng, p).run()
            kicks_done += 1
            if len(cand.routes) <= m.K and cand.cost() < st.cost() - EPS:
                st = cand
        sol = st.to_solution()
        cost = sol.cost(inst)
        feasible = sol.is_feasible(inst)
        if feasible and cost < best_cost - EPS:
            best_sol, best_cost = sol, cost
        history.append(
            {
                "iteration": it,
                "constructed": c_constr,
                "after_ls": cost,
                "best": best_cost,
                "routes": len(sol),
                "feasible": feasible,
                "seconds": time.perf_counter() - t0,
                "kicks": kicks_done,
            }
        )
        if verbose:
            print(f"it {it:3d}  construct {c_constr:9.1f}  LS {cost:9.1f}  best {best_cost:9.1f}")
        if p.time_limit is not None and time.perf_counter() - t0 > p.time_limit:
            break
    return GRASPResult(best_sol, best_cost, time.perf_counter() - t0, it, history)


# --------------------------------------------------------------------------- #
# Traffic mode: exact route evaluation with time-dependent travel times        #
# --------------------------------------------------------------------------- #
Routes = list[list[int]]


class _TimeLimitError(Exception):
    """Raised inside the traffic descent when the time limit is reached."""


def _insertion_traffic(cost, route: list[int], u: int) -> tuple[float, int]:
    """Cheapest feasible position of ``u`` in ``route`` under ``cost``: (delta, position)."""
    base = cost(tuple(route))
    best, best_k = INF, -1
    for k in range(len(route) + 1):
        c = cost((*route[:k], u, *route[k:])) - base
        if c < best:
            best, best_k = c, k
    return best, best_k


def _construct_traffic(m: _Model, cost, rng: random.Random, alpha: float, mode: str) -> Routes:
    """Randomized parallel insertion with an RCL, every insertion evaluated exactly."""
    routes: Routes = []
    unrouted = set(range(1, m.n + 1))
    cand: dict[int, list[tuple[float, int]]] = {u: [] for u in unrouted}

    def open_route() -> None:
        pool = sorted(unrouted, key=lambda c: (-m.D[0][c], m.l[c]))
        if m.tw and rng.random() < 0.5:
            pool = sorted(unrouted, key=lambda c: m.l[c])
        pool = [c for c in pool if math.isfinite(cost((c,)))]
        if not pool:
            raise ValueError("a customer cannot be served alone under traffic: infeasible")
        top = pool[: max(1, int(math.ceil(alpha * len(pool) * 0.2)) + 1)]
        u = rng.choice(top)
        routes.append([u])
        unrouted.discard(u)
        cand.pop(u, None)
        for v in unrouted:
            cand[v].append(_insertion_traffic(cost, routes[-1], v))

    open_route()
    while unrouted:
        scores: list[tuple[float, int]] = []
        for u in unrouted:
            b1 = b2 = INF
            for sc, _ in cand[u]:
                if sc < b1:
                    b1, b2 = sc, b1
                elif sc < b2:
                    b2 = sc
            if b1 == INF:
                continue
            if mode == "regret":
                reg = (b2 - b1) if b2 < INF else 2.0 * m.D[0][u]
                scores.append((b1 - reg, u))
            else:
                scores.append((b1, u))
        if not scores:
            open_route()
            continue
        lo = min(sc for sc, _ in scores)
        hi = max(sc for sc, _ in scores)
        thr = lo + alpha * (hi - lo) + EPS
        u = rng.choice([u for sc, u in scores if sc <= thr])
        opts = cand.pop(u)
        ri = min(range(len(opts)), key=lambda i: opts[i][0])
        routes[ri].insert(opts[ri][1], u)
        unrouted.discard(u)
        for v in unrouted:  # adaptive: only the modified route is re-evaluated
            cand[v][ri] = _insertion_traffic(cost, routes[ri], v)
    return routes


class _LocalSearchTraffic:
    """Granular VND with exact (memoized) route costs: moves change one or two routes."""

    def __init__(self, m: _Model, routes: Routes, cost, rng, p: GRASPParams, deadline) -> None:
        self.m, self.cost, self.rng, self.p, self.deadline = m, cost, rng, p, deadline
        self.routes = [r for r in routes if r]
        self.reindex()
        self.ops = [self._relocate, self._swap, self._two_opt_star, self._or_opt, self._two_opt]

    def reindex(self) -> None:
        """Rebuild ``where[u] = (route index, position)``."""
        self.where = [(-1, -1)] * (self.m.n + 1)
        for ri, r in enumerate(self.routes):
            for k, u in enumerate(r):
                self.where[u] = (ri, k)

    def c(self, r) -> float:
        """Exact cost of one route."""
        return self.cost(tuple(r))

    def run(self) -> None:
        """Descend until no neighborhood improves (or the time limit is reached)."""
        k, moves = 0, 0
        first = self.p.improvement == "first"
        order = list(range(1, self.m.n + 1))
        while k < len(self.ops) and moves < self.p.max_local_rounds:
            if self.deadline is not None and time.perf_counter() > self.deadline:
                raise _TimeLimitError
            op = self.ops[k]
            self.rng.shuffle(order)
            best = None
            for u in order:
                for mv in op(u):
                    if best is None or mv[0] < best[0]:
                        best = mv
                    if first:
                        break
                if first and best is not None:
                    break
            if best is not None:
                self._apply(best[1])
                moves += 1
                k = 0
            else:
                k += 1

    def _apply(self, changes: dict[int, list[int]]) -> None:
        for ri, r in changes.items():
            self.routes[ri] = r
        self.routes = [r for r in self.routes if r]
        self.reindex()

    def _pair(self, ru, nu, rv, nv):
        """Delta of replacing routes ru, rv by nu, nv (None if not improving)."""
        R, T = self.routes[ru], self.routes[rv]
        delta = self.c(nu) + self.c(nv) - self.c(R) - self.c(T)
        return (delta, {ru: nu, rv: nv}) if delta < -EPS else None

    def _single(self, ru, nu):
        delta = self.c(nu) - self.c(self.routes[ru])
        return (delta, {ru: nu}) if delta < -EPS else None

    def _relocate(self, u):
        ru, pu = self.where[u]
        R = self.routes[ru]
        rest = R[:pu] + R[pu + 1 :]
        for v in self.m.neigh[u]:
            rv, pv = self.where[v]
            for k in (pv, pv + 1):  # before or after v
                if rv == ru:
                    kk = k if k <= pu else k - 1
                    mv = self._single(ru, rest[:kk] + [u] + rest[kk:])
                else:
                    T = self.routes[rv]
                    mv = self._pair(ru, rest, rv, T[:k] + [u] + T[k:])
                if mv:
                    yield mv

    def _swap(self, u):
        ru, pu = self.where[u]
        for v in self.m.neigh[u]:
            rv, pv = self.where[v]
            if rv == ru:
                continue
            R, T = self.routes[ru], self.routes[rv]
            mv = self._pair(ru, R[:pu] + [v] + R[pu + 1 :], rv, T[:pv] + [u] + T[pv + 1 :])
            if mv:
                yield mv

    def _two_opt_star(self, u):
        ru, i = self.where[u]
        for v in self.m.neigh[u]:
            rv, j = self.where[v]
            if rv == ru:
                continue
            R, T = self.routes[ru], self.routes[rv]
            mv = self._pair(ru, R[: i + 1] + T[j:], rv, T[:j] + R[i + 1 :])
            if mv:
                yield mv

    def _or_opt(self, u):
        ru, pu = self.where[u]
        R = self.routes[ru]
        for ln in (2, 3):
            if pu + ln > len(R):
                break
            seg, rest = R[pu : pu + ln], R[:pu] + R[pu + ln :]
            for v in self.m.neigh[seg[-1]]:
                rv, pv = self.where[v]
                if rv == ru:
                    continue
                T = self.routes[rv]
                mv = self._pair(ru, rest, rv, T[:pv] + seg + T[pv:])
                if mv:
                    yield mv

    def _two_opt(self, u):
        ru, i = self.where[u]
        R = self.routes[ru]
        for j in range(i + 2, len(R)):
            mv = self._single(ru, R[: i + 1] + R[i + 1 : j + 1][::-1] + R[j + 1 :])
            if mv:
                yield mv


def _reinsert_traffic(m: _Model, cost, routes: Routes, customers: list[int], rng) -> bool:
    """Cheapest exact insertion of each customer; a new route if the fleet allows it."""
    rng.shuffle(customers)
    customers.sort(key=lambda c: m.l[c] - m.e[c])
    for u in customers:
        best, best_ri, best_k = INF, -1, -1
        for ri, r in enumerate(routes):
            c, k = _insertion_traffic(cost, r, u)
            if c < best:
                best, best_ri, best_k = c, ri, k
        if best_ri < 0:
            if len(routes) >= m.K or not math.isfinite(cost((u,))):
                return False
            routes.append([u])
        else:
            routes[best_ri].insert(best_k, u)
    return True


def _kick_traffic(m: _Model, cost, routes: Routes, rng) -> Routes | None:
    """Remove a cluster of 10-20 % of the customers and reinsert them (None if it fails)."""
    k = max(3, int(rng.uniform(0.10, 0.20) * m.n))
    seed = rng.randint(1, m.n)
    near = [seed, *m.neigh[seed]]
    if len(near) < k:
        near += rng.sample(range(1, m.n + 1), k)
    removed = list(dict.fromkeys(near))[:k]
    rem = set(removed)
    new = [[c for c in r if c not in rem] for r in routes]
    new = [r for r in new if r]
    return new if _reinsert_traffic(m, cost, new, removed, rng) else None


def _eliminate_routes_traffic(m: _Model, cost, routes: Routes, rng) -> Routes:
    """Try to empty the smallest routes while the fleet limit is exceeded."""
    tries = 0
    while len(routes) > m.K and tries < 3 * len(routes):
        tries += 1
        ri = min(range(len(routes)), key=lambda i: len(routes[i]))
        trial = [list(r) for i, r in enumerate(routes) if i != ri]
        if not _reinsert_traffic(m, cost, trial, list(routes[ri]), rng):
            break
        routes = trial
    return routes


def _grasp_traffic(inst: Instance, p: GRASPParams, seed, verbose: bool) -> GRASPResult:
    """GRASP minimizing the total route duration with the hourly traffic of notebook 01."""
    rng = random.Random(seed)
    m = _Model(inst, p.n_neighbors)
    cost = cached(duration_cost(inst, start_min=p.start_min))
    t0 = time.perf_counter()
    deadline = None if p.time_limit is None else t0 + p.time_limit
    best_sol, best_cost = None, INF
    history: list[dict] = []
    it = 0

    def total(rs: Routes) -> float:
        return sum(cost(tuple(r)) for r in rs)

    for it in range(1, p.iterations + 1):
        routes = _construct_traffic(m, cost, rng, p.alpha, p.construction)
        c_constr = total(routes)
        if len(routes) > m.K:
            routes = _eliminate_routes_traffic(m, cost, routes, rng)
        ls = _LocalSearchTraffic(m, routes, cost, rng, p, deadline)
        try:
            ls.run()
            for _ in range(p.perturb_kicks):
                if deadline is not None and time.perf_counter() > deadline:
                    break
                cand = _kick_traffic(m, cost, ls.routes, rng)
                if cand is None:
                    continue
                trial = _LocalSearchTraffic(m, cand, cost, rng, p, deadline)
                trial.run()
                if len(trial.routes) <= m.K and total(trial.routes) < total(ls.routes) - EPS:
                    ls = trial
        except _TimeLimitError:
            pass  # keep the routes reached so far: every applied move kept them feasible
        routes = ls.routes
        dur = total(routes)
        sol = Solution([list(r) for r in routes])
        # Exact traffic feasibility (finite duration, fleet) plus the shared evaluator:
        # travel under traffic is never faster than distance, so it must accept the routes too.
        feasible = math.isfinite(dur) and len(routes) <= m.K and sol.is_feasible(inst)
        if feasible and dur < best_cost - EPS:
            best_sol, best_cost = sol, dur
        history.append(
            {
                "iteration": it,
                "constructed": c_constr,
                "after_ls": dur,
                "best": best_cost,
                "distance": sol.cost(inst),
                "routes": len(routes),
                "feasible": feasible,
                "seconds": time.perf_counter() - t0,
            }
        )
        if verbose:
            print(f"it {it:3d}  construct {c_constr:9.1f}  LS {dur:9.1f}  best {best_cost:9.1f}")
        if deadline is not None and time.perf_counter() > deadline:
            break
    return GRASPResult(best_sol, best_cost, time.perf_counter() - t0, it, history)
