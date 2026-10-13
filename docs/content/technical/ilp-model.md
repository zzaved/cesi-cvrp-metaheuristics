---
sidebar_position: 3
title: ILP model
---

# Integer linear programming model

Owner: **Person 1**. Feeds section 6 of notebook 01 and section 3 and 4 of the final deliverable.
Code: `src/cvrp/ilp.py` (TODO P1-06, P1-09). Notation: [Modeling](./modeling.md).

## Two-index formulation with MTZ constraints (CVRP)

**Variables.** $x_{ij} \in \{0, 1\}$ for $(i, j) \in A$, equal to 1 if a truck travels from $i$
to $j$. $u_i \in \mathbb{R}$ for $i \in V^+$, the load on the truck after serving $i$.

**Objective.**

$$
\min \sum_{(i, j) \in A} c_{ij}\, x_{ij}
$$

**Constraints.**

$$
\begin{aligned}
& \sum_{j \in V,\, j \neq i} x_{ij} = 1 && \forall i \in V^+ && \text{(1) leave each customer once}\\
& \sum_{i \in V,\, i \neq j} x_{ij} = 1 && \forall j \in V^+ && \text{(2) enter each customer once}\\
& \sum_{j \in V^+} x_{0j} \le K && && \text{(3) at most } K \text{ trucks}\\
& \sum_{j \in V^+} x_{0j} = \sum_{i \in V^+} x_{i0} && && \text{(4) trucks come back}\\
& u_j \ge u_i + q_j - Q\,(1 - x_{ij}) && \forall i, j \in V^+,\ i \neq j && \text{(5) MTZ load, no subtour}\\
& q_i \le u_i \le Q && \forall i \in V^+ && \text{(6) capacity}\\
& x_{ij} \in \{0, 1\} && \forall (i, j) \in A
\end{aligned}
$$

Constraint (5) (Miller, Tucker and Zemlin, 1960, adapted to loads) forces the load to increase
along every arc between customers, which forbids cycles that do not pass through the depot, and
with (6) bounds the load by $Q$.

Size: $n(n+1)$ binaries, $n$ continuous variables, $O(n^2)$ constraints. **Weakness:** the LP
relaxation of MTZ is weak, so the lower bound is poor and branch and bound slows down quickly.
Expected practical limit with CBC: around $n = 12$ to $20$. **TODO (P1-08):** measure it.

## Stronger alternative: rounded capacity cuts

Replace (5) and (6) by, for every subset of customers $S \subseteq V^+$, $S \ne \emptyset$:

$$
\sum_{i \notin S} \sum_{j \in S} x_{ij} \ \ge\ \left\lceil \frac{\sum_{i \in S} q_i}{Q} \right\rceil .
$$

There are exponentially many, so they are added lazily (cutting plane: solve, find violated sets,
add, repeat). Optional, P1-07. Gives a much better lower bound.

## Optional: three-index formulation

With $x_{ijk} = 1$ if truck $k$ travels $(i, j)$ and $y_{ik} = 1$ if truck $k$ serves $i$, the
capacity becomes $\sum_i q_i\, y_{ik} \le Q$ per truck. It makes per-vehicle constraints explicit
(heterogeneous fleet, per-vehicle shifts) at the cost of $K$ times more variables and symmetry
between identical trucks. Mention in the deliverable as the formulation we did **not** choose, and
why.

## Time window extension (CVRPTW)

Add $t_i \ge 0$, the service start at node $i$:

$$
\begin{aligned}
& t_j \ \ge\ t_i + s_i + c_{ij} - M_{ij}\,(1 - x_{ij}) && \forall i \in V,\ j \in V^+,\ i \neq j && \text{(7) time propagation}\\
& e_i \le t_i \le l_i && \forall i \in V && \text{(8) windows}\\
& t_i + s_i + c_{i0} \le l_0 + M_{i0}\,(1 - x_{i0}) && \forall i \in V^+ && \text{(9) back before the depot closes}
\end{aligned}
$$

with the tightest valid big-M $M_{ij} = \max(0,\ l_i + s_i + c_{ij} - e_j)$.

**Waiting** is built in: (7) is an inequality, so service may start later than the arrival, but
(8) never lets it start before $e_j$. Constraint (7) also eliminates subtours when $c_{ij} + s_i > 0$,
so MTZ (5) is no longer strictly needed, but keeping it helps the solver.

## Bounds we report

| Quantity | How | Role |
| --- | --- | --- |
| Optimal value | ILP solved to optimality (small n) | ground truth for tests and gaps |
| Lower bound | LP relaxation, or best bound when the time limit stops the solver | how far any solution can be from optimal |
| Upper bound | best integer found by the ILP, or the metaheuristic | what we can actually deliver |

## TODO (Person 1)

- [ ] Implement `solve_cvrp_mtz` and test it on the tiny instance (known optimum).
- [ ] Table: n against solve time and gap between bounds, n = 5 to 20.
- [ ] Implement `solve_cvrptw`; test on a truncated Solomon instance (first 10 to 15 customers).
- [ ] Decide PuLP with CBC or OR-Tools (decision at kickoff).
