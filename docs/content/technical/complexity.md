---
sidebar_position: 2
title: Complexity
---

# Complexity

Author: Pablo. Same text as section 2 of the final notebook (`notebooks/02_final_deliverable.ipynb`).

**Decision version (DEC).** Given an instance and a number $B$, is there a feasible plan of total
route duration at most $B$?

**DEC is in NP.** A certificate is the list of routes with each truck's departure time (a rational
of polynomial size: an optimal departure can be taken at a breakpoint of the piecewise linear
schedule). Checking
that every customer appears once, that each load is at most $Q$, and computing the schedule along
each route (one matrix read, one comparison per visit) takes $O(n + K)$ operations; comparing the
total with $B$ is one more.

**Hamiltonian cycle reduces to DEC.** Let $G = (U, E)$ be a graph with $U = \{u_0, \dots, u_m\}$,
$m \ge 2$. Build in $O(m^2)$ the instance: depot $u_0$, customers $u_1, \dots, u_m$, $K = 1$,
$q_i = 1$, $Q = m$, $s_i = 0$, every window equal to the whole day, $\rho_h = 1$ for every $h$,
$c_{ij} = 1/(m+1)$ minute if $\{u_i, u_j\} \in E$ and $c_{ij} = 2/(m+1)$ otherwise, and $B = 1$
(so every plan fits in the day whatever $m$).

- If $G$ has a Hamiltonian cycle, start it at $u_0$: the truck follows it, each of its $m + 1$
  trips takes $1/(m+1)$, no window makes it wait, so the duration is $1 \le B$.
- If a plan has duration at most $1$: the single truck visits the $m$ customers once each and
  returns, so its route is a cycle through all $m + 1$ nodes made of $m + 1$ trips. Each trip takes
  at least $1/(m+1)$, so all of them take exactly $1/(m+1)$, and each one is an edge of $G$: the
  route is a Hamiltonian cycle of $G$.

Hamiltonian cycle is NP-complete (Karp, 1972), so DEC is **NP-complete** and the optimization
problem is **NP-hard**. The instance built uses only the special case $K = 1$, $\rho_h = 1$, wide
windows, which is the travelling salesman problem: capacity, windows and traffic add constraints
to a problem that is already hard. Capacity alone is hard too: deciding whether $K$ trucks can
carry the demands is bin packing (Garey and Johnson, 1979).

**Consequence.** No polynomial exact algorithm is expected. The [ILP model](./ilp-model.md) page measures
where the exact ILP stops being usable; the [metaheuristics](./metaheuristic.md) handle the
realistic sizes.
