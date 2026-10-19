"""Exact approach: integer linear programs for small instances (PuLP with HiGHS).

The formulations are written out in docs/technical/ilp-model and compared in
notebooks/01_modeling_check. Three ways to forbid subtours and enforce capacity
on the same two-index model are implemented:

- ``solve_cvrp_mtz``: Miller-Tucker-Zemlin load variables (compact, weak LP).
- ``solve_cvrp_flow``: single-commodity flow, Gavish and Graves (compact, stronger LP).
- ``solve_cvrp_rcc``: rounded capacity cuts added lazily (exponential family, strongest LP).

``solve_cvrptw`` adds time variables and big-M linking constraints to the flow
model (the formulation chosen in notebook 01) for the Level A problem.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import pulp

from cvrp.instance import Instance
from cvrp.solution import Solution

EPS = 1e-6


@dataclass
class ILPResult:
    """Outcome of an exact solve.

    Attributes:
        status: ``"Optimal"``, ``"TimeLimit"`` (feasible, not proven optimal),
            ``"NoSolution"`` or ``"LP"`` (relaxation solved).
        objective: Best integer objective found (upper bound), or the LP value.
        lower_bound: Best bound proven by the solver (or the LP relaxation).
        solution: Routes decoded from the x variables, if any.
        seconds: Wall clock time of the whole solve.
        n_vars: Number of variables of the (last) model.
        n_constraints: Number of constraints of the (last) model.
        rounds: Number of solver calls (cutting plane rounds; 1 for compact models).
    """

    status: str
    objective: float | None
    lower_bound: float | None
    solution: Solution | None
    seconds: float
    n_vars: int = 0
    n_constraints: int = 0
    rounds: int = 1


def _fleet(inst: Instance) -> int:
    """Upper bound K on the number of routes (n when the instance gives none)."""
    return inst.num_vehicles if inst.num_vehicles is not None else inst.n_customers


def _two_index(inst: Instance, relax: bool) -> tuple[pulp.LpProblem, dict]:
    """Build the part shared by every formulation: x_ij, objective, degrees, fleet.

    Constraints (1) to (4) of the model: leave and enter each customer once,
    at most K routes, every route that leaves the depot comes back.
    """
    n = inst.n_customers
    nodes = range(n + 1)  # 0 is the depot, 1..n are the customers (V+)
    # Binary for the real model; continuous in [0, 1] for the LP relaxation (lower bound).
    cat = pulp.LpContinuous if relax else pulp.LpBinary
    prob = pulp.LpProblem(inst.name.replace("-", "_"), pulp.LpMinimize)
    # x_ij = 1 if some truck drives directly from i to j. One variable per ordered pair i != j:
    # it says whether the trip is used, not which truck uses it, nor how much it carries.
    x = {
        (i, j): prob.add_variable(f"x_{i}_{j}", 0, 1, cat) for i in nodes for j in nodes if i != j
    }
    # Objective: total travel time. c_ij * x_ij counts c_ij only when the trip is used.
    prob += pulp.lpSum(float(inst.dist[i, j]) * var for (i, j), var in x.items())
    for i in range(1, n + 1):
        # (1) exactly one trip leaves customer i
        prob += pulp.lpSum(x[i, j] for j in nodes if j != i) == 1, f"out_{i}"
        # (2) exactly one trip enters customer i
        prob += pulp.lpSum(x[j, i] for j in nodes if j != i) == 1, f"in_{i}"
    # (3) each trip leaving the depot is one truck: at most K of them (K is a limit, not a target)
    prob += pulp.lpSum(x[0, j] for j in range(1, n + 1)) <= _fleet(inst), "fleet"
    # (4) as many trips back into the depot as out of it: every truck comes back
    prob += (
        pulp.lpSum(x[0, j] for j in range(1, n + 1))
        == pulp.lpSum(x[i, 0] for i in range(1, n + 1)),
        "return",
    )
    # (1) to (4) still allow subtours (3 -> 4 -> 3) and overloaded routes: each formulation
    # below adds its own constraints to forbid both.
    return prob, x


def _add_mtz(prob: pulp.LpProblem, x: dict, inst: Instance) -> None:
    """MTZ load constraints (5) and (6): u_j >= u_i + q_j - Q (1 - x_ij), q_i <= u_i <= Q."""
    n, q, cap = inst.n_customers, inst.demands.tolist(), float(inst.capacity)
    # u_i = load already delivered when the truck leaves customer i.
    # (6) is written as variable bounds: q_i <= u_i <= Q.
    u = {i: prob.add_variable(f"u_{i}", float(q[i]), float(cap)) for i in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                # (5) if the truck goes i -> j, the delivered load grows by q_j.
                # (1 - x_ij) is 0 when the trip is used and 1 when it is not, so the
                # "- Q (1 - x_ij)" term vanishes on used trips and switches the constraint
                # off on unused ones (big-M with M = Q). Around a loop of customers u would
                # have to grow forever, which is impossible: no subtours.
                prob += u[j] >= u[i] + q[j] - cap * (1 - x[i, j]), f"mtz_{i}_{j}"


def _add_flow(prob: pulp.LpProblem, x: dict, inst: Instance) -> None:
    """Single-commodity flow: f_ij is the load on board when travelling i -> j.

    Each visit drops q_j, so the flow strictly decreases along a route and no
    cycle of customers can carry a consistent flow. Bounds tie f to x and to Q.
    """
    n, q, cap = inst.n_customers, inst.demands.tolist(), float(inst.capacity)
    f = {}
    for (i, j), var in x.items():
        if j == 0:
            continue  # trucks come back empty: f_i0 = 0, so no variable is needed
        # f_ij >= 0 = load on board while driving from i to j (continuous, not binary).
        f[i, j] = prob.add_variable(f"f_{i}_{j}", 0)
        # (6) lower bound: on a used trip the truck carries at least what j ordered.
        # On an unused trip (x_ij = 0) both bounds give 0 <= f_ij <= 0: no load moves.
        prob += f[i, j] >= q[j] * var, f"flow_lo_{i}_{j}"
        # (6) upper bound: Q - q_i = capacity minus what was just dropped at i, so the load
        # never exceeds Q. Leaving the depot q_0 = 0 and the bound is Q itself.
        prob += f[i, j] <= (cap - q[i]) * var, f"flow_up_{i}_{j}"
    for j in range(1, n + 1):
        inflow = pulp.lpSum(f[i, j] for i in range(n + 1) if i != j)  # load arriving at j
        outflow = pulp.lpSum(f[j, k] for k in range(1, n + 1) if k != j)  # load leaving j
        # (5) flow balance: load in minus load out = what stayed at j, i.e. its demand q_j.
        # Goods only come out of the depot, so a loop of customers has no source of load
        # and cannot satisfy this: no subtours.
        prob += inflow - outflow == q[j], f"flow_bal_{j}"


def _add_rcc(prob: pulp.LpProblem, x: dict, inst: Instance, subset: frozenset, tag: int) -> None:
    """Rounded capacity cut: at least ceil(q(S) / Q) arcs enter the customer set S."""
    # Trucks needed for S: total demand of S divided by Q, rounded up. EPS is subtracted only
    # to absorb floating point noise (e.g. 2.0000001 must round up to 2, not 3).
    need = float(math.ceil(inst.demands[list(subset)].sum() / inst.capacity - EPS))
    # Arcs entering S: from any node i outside S (depot included) to a node j inside S.
    prob += (
        pulp.lpSum(x[i, j] for j in subset for i in range(inst.n_customers + 1) if i not in subset)
        >= need,
        f"rcc_{tag}",
    )


def _solve(prob: pulp.LpProblem, time_limit: float) -> tuple[str, float | None, float | None]:
    """Run HiGHS; return (status, objective, best bound)."""
    # One thread and a time limit, identical for every formulation, so the comparison is fair.
    solver = pulp.HiGHS(msg=False, timeLimit=max(time_limit, 1.0), threads=1)
    stats = prob.solve(solver)
    # obj: best solution found (an upper bound on the optimum).
    obj = pulp.value(prob.objective) if stats.has_solution else None
    # bound: best lower bound proven by branch and bound; for an LP it is the LP value itself.
    # When obj == bound the solution is proven optimal.
    bound = prob.solverModel.getInfo().mip_dual_bound if stats.is_mip else obj
    if bound is not None and not math.isfinite(bound):
        bound = None
    if stats.status == pulp.LpSolveStatus.Optimal:
        return "Optimal", obj, bound
    return ("TimeLimit" if obj is not None else "NoSolution"), obj, bound


def _successors(x: dict) -> dict[int, list[int]]:
    """Return, for each node, the heads of the arcs selected (x_ij > 0.5)."""
    succ: dict[int, list[int]] = {}
    for (i, j), var in x.items():
        if (var.value() or 0.0) > 0.5:
            succ.setdefault(i, []).append(j)
    return succ


def _decode(x: dict, n: int) -> tuple[list[list[int]], list[list[int]]]:
    """Split an integer x into routes through the depot and cycles of customers only."""
    succ = _successors(x)
    seen: set[int] = set()
    routes = []
    # Each arc leaving the depot starts one route: follow the unique successor of every
    # customer (constraint (1)) until the route returns to 0.
    for start in succ.get(0, []):
        route, node = [], start
        while node != 0 and node not in seen:
            seen.add(node)
            route.append(node)
            node = succ[node][0]
        routes.append(route)
    # Customers not reached from the depot lie on subtours (loops that never visit 0).
    cycles = []
    for v in range(1, n + 1):
        if v in seen or v not in succ:
            continue
        cycle, node = [], v
        while node not in seen:
            seen.add(node)
            cycle.append(node)
            node = succ[node][0]
        cycles.append(cycle)
    return routes, cycles


def _components(x: dict, n: int, threshold: float = EPS) -> list[frozenset]:
    """Connected components of the customers, keeping only arcs with x_ij > threshold."""
    parent = list(range(n + 1))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for (i, j), var in x.items():
        if i and j and (var.value() or 0.0) > threshold:
            parent[find(i)] = find(j)
    groups: dict[int, set[int]] = {}
    for v in range(1, n + 1):
        groups.setdefault(find(v), set()).add(v)
    return [frozenset(g) for g in groups.values()]


def _inflow(x: dict, subset: frozenset, n: int) -> float:
    """Sum of x over the arcs that enter the customer set S."""
    return sum(x[i, j].value() or 0.0 for j in subset for i in range(n + 1) if i not in subset)


def _result(prob, x, inst, status, obj, bound, start, rounds=1, relax=False) -> ILPResult:
    """Package a solve into an ILPResult, decoding routes from integer solutions."""
    solution = None
    if obj is not None and not relax:
        routes, _ = _decode(x, inst.n_customers)
        solution = Solution(routes)
    return ILPResult(
        status="LP" if relax and obj is not None else status,
        objective=obj,
        lower_bound=obj if relax else bound,
        solution=solution,
        seconds=time.perf_counter() - start,
        n_vars=prob.numVariables(),
        n_constraints=prob.numConstraints(),
        rounds=rounds,
    )


def solve_cvrp_mtz(inst: Instance, time_limit: float = 60.0, relax: bool = False) -> ILPResult:
    """Solve the two-index CVRP formulation with MTZ load constraints.

    Variables: x_ij binary (arc i -> j used), u_i continuous (load after i).
    With ``relax=True``, x is continuous and the result is the LP lower bound.
    """
    start = time.perf_counter()
    prob, x = _two_index(inst, relax)
    _add_mtz(prob, x, inst)
    status, obj, bound = _solve(prob, time_limit)
    return _result(prob, x, inst, status, obj, bound, start, relax=relax)


def solve_cvrp_flow(inst: Instance, time_limit: float = 60.0, relax: bool = False) -> ILPResult:
    """Solve the two-index CVRP formulation with single-commodity flow (Gavish and Graves).

    Variables: x_ij binary, f_ij continuous (load on board on arc i -> j).
    With ``relax=True``, x is continuous and the result is the LP lower bound.
    """
    start = time.perf_counter()
    prob, x = _two_index(inst, relax)
    _add_flow(prob, x, inst)
    status, obj, bound = _solve(prob, time_limit)
    return _result(prob, x, inst, status, obj, bound, start, relax=relax)


def _violated_fractional(x: dict, inst: Instance, cuts: set[frozenset]) -> list[frozenset]:
    """Heuristic separation of rounded capacity cuts on a fractional x.

    Candidate sets S are the connected components of the customers when only
    arcs with x_ij above a threshold are kept, for a few thresholds (a cheap
    version of the shrinking heuristics of branch and cut codes).
    """
    n, found = inst.n_customers, []
    for threshold in (EPS, 0.3, 0.5, 0.7, 0.99):
        for s in _components(x, n, threshold):
            need = math.ceil(inst.demands[list(s)].sum() / inst.capacity - EPS)
            # Violated: fewer trucks enter S (in the fractional solution) than S needs.
            if s not in cuts and s not in found and _inflow(x, s, n) < need - EPS:
                found.append(s)
    return found


def solve_cvrp_rcc(
    inst: Instance, time_limit: float = 60.0, relax: bool = False, max_rounds: int = 200
) -> ILPResult:
    """Solve the two-index CVRP formulation with rounded capacity cuts added lazily.

    Phase 1 (root): solve the LP relaxation, add violated cuts found by
    ``_violated_fractional``, repeat. Its last value is the lower bound returned
    when ``relax`` is True. Phase 2: solve the integer model with the root cuts,
    and while the integer solution has a cycle of customers (inflow 0) or an
    overloaded route (inflow 1 < ceil(q(S)/Q)), add that cut and solve again.
    Every round solves a relaxation of the CVRP, so the loop stops at a proven
    optimum. PuLP has no lazy constraint callback, so each round restarts
    branch and bound from scratch: this is the weak point of this version.
    """
    start = time.perf_counter()
    n = inst.n_customers
    cuts: set[frozenset] = set()
    rounds = 0

    def left() -> float:
        return time_limit - (time.perf_counter() - start)

    # Phase 1: LP relaxation (x continuous), tightened with cuts until none is found.
    prob, x = _two_index(inst, relax=True)
    lp_bound, status = None, "NoSolution"
    while rounds < max_rounds and left() > 0:
        rounds += 1
        status, obj, _ = _solve(prob, left())
        if status != "Optimal":
            break
        lp_bound = obj
        violated = _violated_fractional(x, inst, cuts)
        if not violated:
            break
        for s in violated:
            _add_rcc(prob, x, inst, s, len(cuts))
            cuts.add(s)
    if relax:
        return ILPResult(
            "LP" if lp_bound is not None else status,
            lp_bound,
            lp_bound,
            None,
            time.perf_counter() - start,
            prob.numVariables(),
            prob.numConstraints(),
            rounds,
        )

    # Phase 2: integer model (x binary) with the cuts of phase 1, then the referee loop.
    prob, x = _two_index(inst, relax=False)
    for tag, s in enumerate(cuts):
        _add_rcc(prob, x, inst, s, tag)
    best_bound = lp_bound
    while rounds < max_rounds and left() > 0:
        rounds += 1
        status, obj, bound = _solve(prob, left())
        if bound is not None and (best_bound is None or bound > best_bound):
            best_bound = bound
        if status != "Optimal":
            break
        routes, cycles = _decode(x, n)
        # Every subtour (inflow 0 < 1) and every overloaded route (inflow 1 < 2 or more)
        # breaks a cut (5C): add it and solve again.
        heavy = [r for r in routes if inst.demands[r].sum() > inst.capacity + EPS]
        violated = [frozenset(s) for s in cycles + heavy]
        if not violated:
            # Optimal for a relaxation of the CVRP and feasible for the CVRP: proven optimal.
            return _result(prob, x, inst, status, obj, obj, start, rounds)
        for s in violated:
            _add_rcc(prob, x, inst, s, len(cuts))
            cuts.add(s)
    # Stopped before convergence: the last integer x may be infeasible, so report no solution.
    return ILPResult(
        "TimeLimit",
        None,
        best_bound,
        None,
        time.perf_counter() - start,
        prob.numVariables(),
        prob.numConstraints(),
        rounds,
    )


def solve_cvrptw(inst: Instance, time_limit: float = 60.0, relax: bool = False) -> ILPResult:
    """Solve the CVRPTW: flow model plus time variables and big-M linking constraints.

    t_j >= t_i + s_i + c_ij - M_ij (1 - x_ij), e_i <= t_i <= l_i, waiting allowed,
    with the tightest valid M_ij = max(0, l_i + s_i + c_ij - e_j).
    """
    if not inst.has_time_windows:
        raise ValueError("solve_cvrptw needs an instance with time windows")
    start = time.perf_counter()
    n = inst.n_customers
    ready, due, c = inst.ready_times.tolist(), inst.due_times.tolist(), inst.dist.tolist()
    s = inst.service_times.tolist() if inst.service_times is not None else [0.0] * (n + 1)
    # Core (1) to (4) plus the flow (5) and (6) of the chosen formulation B: capacity.
    prob, x = _two_index(inst, relax)
    _add_flow(prob, x, inst)
    # t_i = time service starts at i. (8) windows written as bounds: e_i <= t_i <= l_i.
    t = {i: prob.add_variable(f"t_{i}", ready[i], due[i]) for i in range(n + 1)}
    for i in range(n + 1):
        for j in range(1, n + 1):
            if i != j:
                # Smallest M that switches (7) off when x_ij = 0: the latest finish-and-drive
                # time from i (l_i + s_i + c_ij) minus the earliest start at j (e_j). With it,
                # the right side is at most e_j, which t_j always satisfies.
                big_m = max(0.0, due[i] + s[i] + c[i][j] - ready[j])
                # (7) if the truck goes i -> j, service at j starts after service at i ends
                # and the drive is done. ">=" (not "=") is what allows waiting.
                prob += t[j] >= t[i] + s[i] + c[i][j] - big_m * (1 - x[i, j]), f"time_{i}_{j}"
    for i in range(1, n + 1):
        # Same idea for the return: latest arrival at the depot from i minus closing time l_0.
        big_m = max(0.0, due[i] + s[i] + c[i][0] - due[0])
        # (9) a truck that ends its route at i is back before the depot closes.
        prob += t[i] + s[i] + c[i][0] <= due[0] + big_m * (1 - x[i, 0]), f"back_{i}"
    status, obj, bound = _solve(prob, time_limit)
    return _result(prob, x, inst, status, obj, bound, start, relax=relax)
