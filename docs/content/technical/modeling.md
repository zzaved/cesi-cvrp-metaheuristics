---
sidebar_position: 1
title: Modeling
---

# Formal modeling

Owner: **Person 1**. Feeds section 2 to 4 of `notebooks/01_modeling_check.ipynb`.

:::note[Draft]
Notation and definitions are proposed here and must be checked at the modeling deliverable. Items
marked TODO are for Person 1.

:::

## Data

| Symbol | Meaning |
| --- | --- |
| $V = \{0, 1, \dots, n\}$ | Nodes; $0$ is the depot |
| $V^+ = V \setminus \{0\}$ | Customers |
| $A = \{(i, j) \in V \times V : i \neq j\}$ | Arcs of the complete directed graph $G = (V, A)$ |
| $c_{ij} \ge 0$ | Travel time from $i$ to $j$ (shortest path on the road network) |
| $q_i > 0$ | Demand of customer $i$, with $q_0 = 0$ and $q_i \le Q$ |
| $Q$ | Capacity of every truck |
| $K$ | Number of available trucks |
| $[e_i, l_i]$ | Time window of node $i$ (Level A); $[e_0, l_0]$ is the working day |
| $s_i \ge 0$ | Service time at node $i$ (Level A), $s_0 = 0$ |

In code: `Instance.coords`, `demands`, `capacity`, `num_vehicles`, `ready_times`, `due_times`,
`service_times`, `dist` (see [Architecture](./architecture.md)).

## From a road network to a complete graph

The real network is a sparse graph of roads. We replace it by the complete graph $G$ whose arc
cost $c_{ij}$ is the duration of the fastest path from $i$ to $j$. Two consequences:

1. The triangle inequality holds, so a route never benefits from visiting a node twice.
2. In benchmarks, $c_{ij}$ is the Euclidean distance between coordinates (unit speed), so
   duration and distance coincide.

**Traffic per time slot (extension).** With traffic, $c_{ij}$ becomes $c_{ij}(t)$, a function of
the departure time $t$. A standard way to keep it consistent (no overtaking, FIFO) is to make
*speeds* piecewise constant by time slot (Ichoua et al., 2003, *to verify*). We keep it out of the
base model and describe it as an improvement.

## CVRP (Level B)

A **route** is a sequence $r = (0, v_1, \dots, v_m, 0)$ of distinct customers. Its load and cost
are

$$
q(r) = \sum_{t=1}^{m} q_{v_t},
\qquad
c(r) = c_{0 v_1} + \sum_{t=1}^{m-1} c_{v_t v_{t+1}} + c_{v_m 0}.
$$

A **solution** is a set of at most $K$ routes $\{r_1, \dots, r_p\}$ such that every customer
appears in exactly one route and $q(r_k) \le Q$ for every $k$. The problem is

$$
\min \sum_{k=1}^{p} c(r_k).
$$

## CVRPTW (Level A)

Along a route, let $a_{v_t}$ be the arrival time and $b_{v_t}$ the service start:

$$
b_0 = e_0, \qquad
a_{v_t} = b_{v_{t-1}} + s_{v_{t-1}} + c_{v_{t-1} v_t}, \qquad
b_{v_t} = \max(a_{v_t},\ e_{v_t}).
$$

The route is feasible when $b_{v_t} \le l_{v_t}$ for every visited node, including the return to
the depot. The waiting time is $w_{v_t} = b_{v_t} - a_{v_t} \ge 0$. The objective is unchanged
(total travel time); waiting is allowed but not counted. *To confirm with the tutor.*

In code: `timewindows.route_schedule` computes exactly $a$, $b$ and $w$.

## Hypothesis 4, revisited

With $K = 1$ and $Q \ge \sum_i q_i$, a solution is a single cycle through every node: a
Hamiltonian cycle, and the problem is the TSP. With several trucks, the solution is a set of
cycles that share the depot and partition the customers. See
[Complexity](./complexity.md).

## TODO (Person 1)

- [ ] Worked example on the 6 customer instance of notebook 01 with one feasible solution and its cost.
- [ ] Decide fixed $K$ (from the instance) or free $K$; justify.
- [ ] Decide whether the objective at Level A includes waiting time.
