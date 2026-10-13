"""Local search neighborhoods: 2-opt, relocate, swap, Or-opt, cross-exchange.

Every move returns True when it improved the solution in place. Deltas are
computed with numpy over all candidate positions at once instead of nested
Python loops.
"""

from __future__ import annotations

import numpy as np

from cvrp.instance import Instance
from cvrp.solution import Solution
from cvrp.timewindows import is_route_tw_feasible

EPS = 1e-9


def two_opt_route(route: list[int], inst: Instance) -> tuple[list[int], bool]:
    """Apply best-improvement 2-opt to one route until no move improves it.

    Reversing the segment between edges (a_i, b_i) and (a_j, b_j) changes the
    cost by d[a_i, a_j] + d[b_i, b_j] - d[a_i, b_i] - d[a_j, b_j].

    Returns:
        The improved route and whether it changed.
    """
    d = inst.dist
    path = np.array([0, *route, 0], dtype=np.intp)
    changed = False
    while len(path) > 4:
        a, b = path[:-1], path[1:]
        delta = d[np.ix_(a, a)] + d[np.ix_(b, b)] - d[a, b][:, None] - d[a, b][None, :]
        delta = np.triu(delta, k=2)  # only j >= i + 2 is a real move
        order = np.argsort(delta, axis=None)
        improved = False
        for flat in order:
            i, j = np.unravel_index(flat, delta.shape)
            if delta[i, j] >= -EPS:
                break
            cand = np.concatenate([path[: i + 1], path[i + 1 : j + 1][::-1], path[j + 1 :]])
            if inst.has_time_windows and not is_route_tw_feasible(cand[1:-1].tolist(), inst):
                continue
            path, improved, changed = cand, True, True
            break
        if not improved:
            break
    return path[1:-1].tolist(), changed


def two_opt(sol: Solution, inst: Instance) -> bool:
    """Apply intra-route 2-opt to every route of the solution."""
    any_change = False
    for k, route in enumerate(sol.routes):
        sol.routes[k], changed = two_opt_route(route, inst)
        any_change |= changed
    return any_change


def relocate(sol: Solution, inst: Instance) -> bool:
    """Move single customers to their best position, in any route (intra and inter).

    For each customer u, the removal gain d[p,u] + d[u,n] - d[p,n] is compared
    with the insertion cost d[a,u] + d[u,b] - d[a,b] over every edge (a, b) of
    the solution at once. The first customer with an improving move is moved.

    TODO(Person 2): restrict candidate edges to the k nearest neighbors of u
    (granular neighborhood) to scale to thousands of customers.
    """
    d = inst.dist
    loads = sol.loads(inst)
    starts = np.concatenate([[0, *r] for r in sol.routes]).astype(np.intp)
    ends = np.concatenate([[*r, 0] for r in sol.routes]).astype(np.intp)
    owner = np.concatenate([[k] * (len(r) + 1) for k, r in enumerate(sol.routes)])

    for k, route in enumerate(sol.routes):
        for pos, u in enumerate(route):
            prev = route[pos - 1] if pos > 0 else 0
            nxt = route[pos + 1] if pos + 1 < len(route) else 0
            gain = d[prev, u] + d[u, nxt] - d[prev, nxt]
            ins = d[starts, u] + d[u, ends] - d[starts, ends]
            fits = (owner == k) | (loads[owner] + inst.demands[u] <= inst.capacity + EPS)
            touches = (starts == u) | (ends == u)
            ins = np.where(fits & ~touches, ins, np.inf)
            best = int(np.argmin(ins))
            if ins[best] - gain >= -EPS:
                continue
            target = int(owner[best])
            new_src = route[:pos] + route[pos + 1 :]
            dst = new_src if target == k else sol.routes[target].copy()
            a = int(starts[best])
            dst.insert(0 if a == 0 else dst.index(a) + 1, u)
            if inst.has_time_windows and not (
                is_route_tw_feasible(dst, inst) and is_route_tw_feasible(new_src, inst)
            ):
                continue
            sol.routes[k] = dst if target == k else new_src
            if target != k:
                sol.routes[target] = dst
            sol.remove_empty_routes()
            return True
    return False


def swap(sol: Solution, inst: Instance) -> bool:
    """Exchange two customers, in the same route or in two routes.

    TODO(Person 2): implement with a vectorized delta over all pairs (u, v).
    """
    raise NotImplementedError


def or_opt(sol: Solution, inst: Instance, max_len: int = 3) -> bool:
    """Move a chain of 1 to ``max_len`` consecutive customers elsewhere.

    TODO(Person 2): implement; also try the reversed chain.
    """
    raise NotImplementedError


def cross_exchange(sol: Solution, inst: Instance, max_len: int = 3) -> bool:
    """Swap two segments of up to ``max_len`` customers between two routes.

    TODO(Person 2): implement (Taillard et al., 1997).
    """
    raise NotImplementedError


def local_search(sol: Solution, inst: Instance, max_rounds: int = 1000) -> Solution:
    """Variable neighborhood descent with the implemented operators.

    Applies relocate until it stops improving, then 2-opt, and restarts while
    anything changes.

    TODO(Person 2): add swap, Or-opt and cross-exchange once implemented.
    """
    for _ in range(max_rounds):
        moved = False
        while relocate(sol, inst):
            moved = True
        moved |= two_opt(sol, inst)
        if not moved:
            break
    return sol
