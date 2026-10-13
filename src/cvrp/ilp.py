"""Exact approach: integer linear programs for small instances (PuLP with CBC).

The formulation is written out in docs/technical/ilp-model. This module turns
it into code so the exact approach can be applied to small instances: direct
solution, lower bound from the LP relaxation, and an upper bound to compare
with the metaheuristic.
"""

from __future__ import annotations

from dataclasses import dataclass

from cvrp.instance import Instance
from cvrp.solution import Solution


@dataclass
class ILPResult:
    """Outcome of an exact solve.

    Attributes:
        status: Solver status string (``"Optimal"``, ``"Not Solved"``, ...).
        objective: Best integer objective found (upper bound), if any.
        lower_bound: Best bound proven by the solver (or the LP relaxation).
        solution: Routes decoded from the x variables, if any.
        seconds: Solve time.
    """

    status: str
    objective: float | None
    lower_bound: float | None
    solution: Solution | None
    seconds: float


def solve_cvrp_mtz(inst: Instance, time_limit: float = 60.0, relax: bool = False) -> ILPResult:
    """Solve the two-index CVRP formulation with MTZ load constraints.

    Variables: x_ij binary (arc i -> j used), u_i continuous (load after i).
    Objective: minimize sum d_ij x_ij.
    Constraints: one arc in and one arc out per customer; at most k arcs leave
    the depot; u_j >= u_i + q_j - Q (1 - x_ij); q_i <= u_i <= Q.

    TODO(Person 1): implement with ``pulp.LpProblem``; when ``relax`` is True,
    use continuous x to get the LP lower bound. Decode routes by following
    successors from the depot. Validate on instances with n <= 15.
    """
    raise NotImplementedError("the ILP is not implemented yet")


def solve_cvrptw(inst: Instance, time_limit: float = 60.0) -> ILPResult:
    """Solve the CVRPTW with time variables and big-M linking constraints.

    t_j >= t_i + s_i + d_ij - M (1 - x_ij), e_i <= t_i <= l_i, waiting allowed.

    TODO(Person 1): implement once ``solve_cvrp_mtz`` is validated.
    """
    raise NotImplementedError("the CVRPTW ILP is not implemented yet")
