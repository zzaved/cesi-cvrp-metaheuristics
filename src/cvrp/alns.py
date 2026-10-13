"""Adaptive Large Neighborhood Search (Ropke and Pisinger, 2006) with SA acceptance.

Each iteration destroys part of the current solution, repairs it, and accepts
the result with the simulated annealing criterion. Operators are picked by a
roulette wheel whose weights adapt to how well each operator performed in the
last segment of iterations.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from cvrp.construct import nearest_neighbor
from cvrp.instance import Instance
from cvrp.sa import accept, initial_temperature
from cvrp.solution import Solution
from cvrp.timewindows import is_route_tw_feasible

DestroyOp = Callable[[Solution, Instance, int, np.random.Generator], list[int]]
RepairOp = Callable[[Solution, list[int], Instance, np.random.Generator], None]


# --------------------------------------------------------------------------- destroy


def random_removal(sol: Solution, inst: Instance, q: int, rng: np.random.Generator) -> list[int]:
    """Remove ``q`` customers chosen uniformly at random. Modifies ``sol`` in place."""
    customers = np.concatenate([np.asarray(r) for r in sol.routes if r])
    removed = rng.choice(customers, size=min(q, len(customers)), replace=False).tolist()
    _remove(sol, set(removed))
    return removed


def worst_removal(
    sol: Solution, inst: Instance, q: int, rng: np.random.Generator, p: float = 3.0
) -> list[int]:
    """Remove customers whose removal saves the most, with randomness controlled by ``p``.

    The gain of removing u between p and n is d[p,u] + d[u,n] - d[p,n]. Sorting
    gains and picking index floor(y^p * len) with y uniform biases the choice
    towards the worst placed customers without being deterministic.
    """
    d = inst.dist
    removed: list[int] = []
    for _ in range(q):
        cust, gains = [], []
        for r in sol.routes:
            if not r:
                continue
            path = np.array([0, *r, 0])
            g = d[path[:-2], path[1:-1]] + d[path[1:-1], path[2:]] - d[path[:-2], path[2:]]
            cust.extend(r)
            gains.extend(g.tolist())
        if not cust:
            break
        order = np.argsort(gains)[::-1]
        pick = cust[order[int(rng.random() ** p * len(order))]]
        _remove(sol, {pick})
        removed.append(pick)
    return removed


def shaw_removal(sol: Solution, inst: Instance, q: int, rng: np.random.Generator) -> list[int]:
    """Related removal (Shaw, 1998): remove customers similar to a random seed customer.

    Relatedness combines distance, demand difference and, for CVRPTW, the
    difference of window starts.

    TODO(Person 2): implement and register in ``DEFAULT_DESTROY``.
    """
    raise NotImplementedError


def _remove(sol: Solution, customers: set[int]) -> None:
    """Delete the given customers from every route and drop empty routes."""
    sol.routes = [[c for c in r if c not in customers] for r in sol.routes]
    sol.remove_empty_routes()


# --------------------------------------------------------------------------- repair


def greedy_insertion(
    sol: Solution, removed: list[int], inst: Instance, rng: np.random.Generator
) -> None:
    """Insert each removed customer, in random order, at its cheapest feasible position.

    A new route is opened when no existing route can take the customer.
    """
    d = inst.dist
    for u in rng.permutation(removed).tolist():
        loads = sol.loads(inst)
        best: tuple[float, int, int] | None = None
        for k, r in enumerate(sol.routes):
            if loads[k] + inst.demands[u] > inst.capacity:
                continue
            path = np.array([0, *r, 0])
            costs = d[path[:-1], u] + d[u, path[1:]] - d[path[:-1], path[1:]]
            for pos in np.argsort(costs):
                if best is not None and costs[pos] >= best[0]:
                    break
                cand = [*r[:pos], u, *r[pos:]]
                if inst.has_time_windows and not is_route_tw_feasible(cand, inst):
                    continue
                best = (float(costs[pos]), k, int(pos))
                break
        if best is None:
            sol.routes.append([u])
        else:
            _, k, pos = best
            sol.routes[k].insert(pos, u)


def regret_insertion(
    sol: Solution, removed: list[int], inst: Instance, rng: np.random.Generator, k: int = 2
) -> None:
    """Regret-k insertion: insert first the customer that would lose most by waiting.

    The regret of u is the sum over its k best routes of (cost in that route
    minus cost in its best route).

    TODO(Person 2): implement and register in ``DEFAULT_REPAIR``.
    """
    raise NotImplementedError


DEFAULT_DESTROY: dict[str, DestroyOp] = {
    "random": random_removal,
    "worst": worst_removal,
}
DEFAULT_REPAIR: dict[str, RepairOp] = {
    "greedy": greedy_insertion,
}


# --------------------------------------------------------------------------- engine


@dataclass
class ALNSParams:
    """Tunable parameters. Defaults follow Ropke and Pisinger (2006) where it applies.

    Attributes:
        iterations: Maximum number of iterations.
        time_limit: Wall-clock limit in seconds (``None`` for no limit).
        destroy_min: Minimum fraction of customers removed per iteration.
        destroy_max: Maximum fraction of customers removed per iteration.
        segment: Iterations between two weight updates.
        reaction: Reaction factor r in w = (1 - r) w + r * score / uses.
        sigma: Scores for (new global best, better than current, accepted worse).
        worse_pct: Used to calibrate the initial temperature.
        cooling: Geometric cooling rate applied every iteration.
    """

    iterations: int = 5000
    time_limit: float | None = None
    destroy_min: float = 0.1
    destroy_max: float = 0.3
    segment: int = 100
    reaction: float = 0.1
    sigma: tuple[float, float, float] = (33.0, 9.0, 13.0)
    worse_pct: float = 0.05
    cooling: float = 0.99975


@dataclass
class ALNSResult:
    """Output of a run: best solution plus the traces needed for the experimental study."""

    best: Solution
    best_cost: float
    iterations: int
    seconds: float
    best_history: list[float] = field(default_factory=list)
    current_history: list[float] = field(default_factory=list)
    destroy_weights: dict[str, float] = field(default_factory=dict)
    repair_weights: dict[str, float] = field(default_factory=dict)


def alns(
    inst: Instance,
    params: ALNSParams | None = None,
    seed: int | None = 0,
    initial: Solution | None = None,
    destroy_ops: dict[str, DestroyOp] | None = None,
    repair_ops: dict[str, RepairOp] | None = None,
) -> ALNSResult:
    """Run ALNS and return the best solution found.

    Args:
        inst: Instance to solve.
        params: Parameters; defaults are used when ``None``.
        seed: Random seed, so every run is reproducible.
        initial: Starting solution; nearest neighbor when ``None``.
        destroy_ops: Named destroy operators.
        repair_ops: Named repair operators.
    """
    params = params or ALNSParams()
    rng = np.random.default_rng(seed)
    destroy_ops = destroy_ops or DEFAULT_DESTROY
    repair_ops = repair_ops or DEFAULT_REPAIR
    d_names, r_names = list(destroy_ops), list(repair_ops)
    d_w, r_w = np.ones(len(d_names)), np.ones(len(r_names))
    d_score, r_score = np.zeros(len(d_names)), np.zeros(len(r_names))
    d_uses, r_uses = np.zeros(len(d_names)), np.zeros(len(r_names))

    current = initial.copy() if initial is not None else nearest_neighbor(inst)
    current_cost = current.cost(inst)
    best, best_cost = current.copy(), current_cost
    temperature = initial_temperature(current_cost, params.worse_pct)
    n = inst.n_customers
    q_lo = max(1, int(params.destroy_min * n))
    q_hi = max(q_lo, int(params.destroy_max * n))

    result = ALNSResult(best=best, best_cost=best_cost, iterations=0, seconds=0.0)
    start = time.perf_counter()
    it = 0
    for it in range(1, params.iterations + 1):
        if params.time_limit is not None and time.perf_counter() - start > params.time_limit:
            break
        di = int(rng.choice(len(d_names), p=d_w / d_w.sum()))
        ri = int(rng.choice(len(r_names), p=r_w / r_w.sum()))
        q = int(rng.integers(q_lo, q_hi + 1))

        candidate = current.copy()
        removed = destroy_ops[d_names[di]](candidate, inst, q, rng)
        repair_ops[r_names[ri]](candidate, removed, inst, rng)
        cand_cost = candidate.cost(inst)

        score = 0.0
        if cand_cost < best_cost - 1e-9 and candidate.is_feasible(inst):
            best, best_cost = candidate.copy(), cand_cost
            current, current_cost = candidate, cand_cost
            score = params.sigma[0]
        elif accept(cand_cost - current_cost, temperature, rng):
            score = params.sigma[1] if cand_cost < current_cost else params.sigma[2]
            current, current_cost = candidate, cand_cost
        d_score[di] += score
        r_score[ri] += score
        d_uses[di] += 1
        r_uses[ri] += 1

        if it % params.segment == 0:
            d_w = _update_weights(d_w, d_score, d_uses, params.reaction)
            r_w = _update_weights(r_w, r_score, r_uses, params.reaction)
            d_score[:], r_score[:], d_uses[:], r_uses[:] = 0, 0, 0, 0

        temperature *= params.cooling
        result.best_history.append(best_cost)
        result.current_history.append(current_cost)

    result.best, result.best_cost = best, best_cost
    result.iterations, result.seconds = it, time.perf_counter() - start
    result.destroy_weights = dict(zip(d_names, d_w.tolist(), strict=True))
    result.repair_weights = dict(zip(r_names, r_w.tolist(), strict=True))
    return result


def _update_weights(
    weights: np.ndarray, scores: np.ndarray, uses: np.ndarray, reaction: float
) -> np.ndarray:
    """Blend old weights with the average score of the last segment (unused ops keep theirs)."""
    used = uses > 0
    new = weights.copy()
    new[used] = (1 - reaction) * weights[used] + reaction * scores[used] / uses[used]
    return np.maximum(new, 1e-3)
