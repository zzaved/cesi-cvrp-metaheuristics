---
sidebar_position: 1
title: Modeling
---

# Formal model

Author: Pablo. Same text as sections 1 and 3 of the final notebook (`notebooks/02_final_deliverable.ipynb`); the toy example
with numbers is in `notebooks/01_modeling_check.ipynb`.

## Data and decision variables

The road network is reduced to a **complete directed graph** on the depot and the customers; the
time of a trip $i \to j$ is the fastest path in the network, computed once. The depot appears
twice, node $0$ (departure) and node $n + 1$ (return), so each truck has a departure and a return
time. All times are minutes after midnight.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| $V^+ = \{1, \dots, n\}$ | customers | |
| $V = \{0\} \cup V^+ \cup \{n+1\}$ | nodes; $0$ and $n+1$ are the depot | |
| $A$ | trips: depot to customer, customer to customer, customer to depot, and $0 \to n+1$ (truck not used) | |
| $\mathcal{K} = \{1, \dots, K\}$ | identical trucks | |
| $\mathcal{H} = \{0, \dots, 23\}$ | hours of the day | |
| $Q$ | capacity of a truck | units |
| $q_i$ | demand of customer $i$ ($q_i \le Q$) | units |
| $[e_i, l_i]$ | time window: service must **start** in it | min |
| $s_i$ | service time at customer $i$ ($s_0 = 0$) | min |
| $[e_0, l_0]$ | working day of the depot | min |
| $c_{ij}$ | travel time from $i$ to $j$ on empty roads | min |
| $\rho_h$ | traffic intensity of hour $h$ ($\rho_h \ge 1$) | |
| $c_{ij}^h = \rho_h \, c_{ij}$ | **traffic matrix**: travel time when leaving $i$ during hour $h$ | min |

The $\rho_h$ values (peaks 1.75 to 1.80 from 7:00 to 9:00 and from 17:00 to 19:00, 1.00 at night)
are assumptions of notebook 01, to be replaced by measured data. The model only reads numbers from
the matrix, so measured values change no equation.

**Decision variables**

| Variable | Domain | Meaning |
| --- | --- | --- |
| $x_{ij}^k$ | $\{0, 1\}$ | truck $k$ drives directly from $i$ to $j$ |
| $y_{ih}$, $y_{0h}^k$ | $\{0, 1\}$ | the truck leaves customer $i$ (the depot, for truck $k$) during hour $h$ |
| $t_0^k$, $t_{n+1}^k$ | $\ge 0$, min | truck $k$ leaves the depot, is back |
| $a_i$, $w_i$, $t_i$ | $\ge 0$, min | arrival, waiting and service start at customer $i$ |

The travel time is fixed by the hour of departure, so a later departure may arrive earlier (the
first in, first out property is not guaranteed): an accepted simplification.

**Benchmark data.** The Solomon instances (56 files, 100 customers, PyVRP/VRPLIB copy) give
$c_{ij}$ as Euclidean distances truncated to one decimal, the convention of their best known
values, and no traffic ($\rho_h = 1$).

## The complete model

$$
\begin{aligned}
\min \quad & z = \sum_{k \in \mathcal{K}} \big( t_{n+1}^k - t_0^k \big) \\[4pt]
\text{s.t.} \quad
& \sum_{k} \sum_{j : (i, j) \in A} x_{ij}^k = 1 && \forall i \in V^+ && \text{(1) each customer served once}\\
& \sum_{j} x_{0j}^k = 1, \quad \sum_{i} x_{i, n+1}^k = 1 && \forall k && \text{(2), (4) each truck leaves and returns}\\
& \sum_{i} x_{ij}^k = \sum_{i} x_{ji}^k && \forall j \in V^+,\ k && \text{(3) a truck that enters leaves}\\
& \sum_{i \in V^+} q_i \sum_{j} x_{ij}^k \le Q && \forall k && \text{(5) capacity}\\
& \sum_h y_{ih} = 1, \quad \sum_h 60h\, y_{ih} \le t_i + s_i \le \sum_h 60(h+1)\, y_{ih} && \forall i \in V^+ && \text{(6), (7) departure hour}\\
& \sum_h y_{0h}^k = 1, \quad \sum_h 60h\, y_{0h}^k \le t_0^k \le \sum_h 60(h+1)\, y_{0h}^k && \forall k && \text{(6), (7) at the depot}\\
& \Big\lvert\, a_j^k - t_i^k - s_i - \sum_h c_{ij}^h\, y_{ih}^k \,\Big\rvert \le M (1 - x_{ij}^k) && \forall (i, j) \in A,\ k && \text{(8) arrival with traffic}\\
& t_i = a_i + w_i, \quad e_i \le t_i \le l_i && \forall i \in V^+ && \text{(9), (10) wait, then serve}\\
& t_0^k \ge e_0, \quad t_{n+1}^k \le l_0 && \forall k && \text{(10) working day}\\
& x,\ y \in \{0, 1\}, \quad a,\ w,\ t \ge 0 && && \text{(11)}
\end{aligned}
$$

Shorthands in (8): $t_i^k$ is $t_i$ at a customer and $t_0^k$ at the depot, $a_j^k$ is $a_j$ at a
customer and $t_{n+1}^k$ at the return, $y_{ih}^k$ is $y_{ih}$ at a customer and $y_{0h}^k$ at the
depot. $M = 2880$ (two days) exceeds every possible value of
$\lvert a_j - t_i - s_i - c_{ij}^h \rvert$ within a working day, so (8) is inactive when
$x_{ij}^k = 0$. The absolute value stands for two linear inequalities; since $c_{ij}^h + s_i > 0$,
times increase along a route and (8) also forbids subtours. $w_i$ is kept so that the waiting
appears in the solution; it could be replaced by $t_i \ge a_i$. Every line is linear: the model is a mixed
integer linear program with $K \lvert A \rvert$ variables $x$, $24 (n + K)$ variables $y$ and
$3n + 2K$ real variables.

**Reading the model line by line.** A sum $\sum_{k}$ adds over the trucks, $\sum_{j : (i,j) \in A}$
over the allowed next stops after $i$, $\sum_h$ over the hours of the day; $\forall$ means the line
is written once for each element of the set.

| Line | In words | Why it is needed |
| --- | --- | --- |
| objective | add, over the trucks, return time minus departure time | the brief asks for the minimum total route duration; one component |
| (1) | for each customer, exactly one arc leaves it, over all trucks | every customer is served, once, by one truck |
| (2) | each truck takes exactly one arc out of the depot (possibly $0 \to n+1$, unused) | each truck has one route; fewer than $K$ trucks are allowed |
| (3) | for each customer and truck, arcs in = arcs out | a truck that reaches a customer leaves it: routes are paths |
| (4) | each truck takes exactly one arc into the return depot | every route ends at the depot |
| (5) | the demands of the customers truck $k$ leaves from add up to at most $Q$ | the load of a truck, full at departure, fits its capacity |
| (6) | exactly one departure hour per stop | picks which value of the traffic matrix applies |
| (7) | the departure time lies inside that hour | ties the hour $h$ to the clock time |
| (8) | if truck $k$ drives $i \to j$, arrival at $j$ = departure from $i$ + travel time of the departure hour | traffic enters the times; switched off by $M$ when the arc is unused; forbids subtours |
| (9) | service start = arrival + waiting | a truck may wait for a window to open |
| (10) | service starts inside the window; trucks work inside the day | time windows and working day |
| (11) | $x, y$ binary, times non-negative | domains |

## What the code solves

Code: `src/cvrp/ilp.py`.

| Function | Model | Used for |
| --- | --- | --- |
| `solve_tdvrptw` | the model above, constraints (1) to (11) | exact optimum with traffic, small $n$ |
| `solve_cvrptw` | benchmark variant: $\rho_h = 1$, two-index $x_{ij}$, objective replaced by total distance $\sum c_{ij} x_{ij}$ | the Solomon benchmark |
| `solve_cvrp_flow`, `_rcc`, `_mtz` | the same variant without windows | CVRP, lower bounds |

The Solomon best known values minimize **total distance** with travel time equal to distance and
no traffic. With $\rho_h = 1$ our objective equals that distance plus the service times (a
constant) plus the waiting, so the benchmark variant optimizes our objective without its waiting
term: it measures the routing part of the model, the only one for which published optima exist. The metaheuristics take the route cost as a function, so the
same search runs on the duration with traffic (`cvrp.tabu.duration_cost`, GRASP
`objective="duration"`).

On the toy instance of notebook 01, `solve_tdvrptw` proves the optimum 247.16 min, the value
found by enumerating every partition, order and departure time; the hand solution took 256.5 min.

## Glossary of symbols

**Model**

| Symbol | Meaning | Unit or domain |
| --- | --- | --- |
| $n$ | number of customers | integer |
| $V^+ = \{1, \dots, n\}$ | customers | set |
| $0$, $n + 1$ | the depot as departure and as return | nodes |
| $V$ | all nodes, $\{0\} \cup V^+ \cup \{n+1\}$ | set |
| $A$ | allowed trips (arcs) $(i, j)$ | set of pairs |
| $\mathcal{K}$, $K$ | the trucks, their number | set, integer |
| $\mathcal{H}$, $h$ | hours of the day, one hour | $\{0, \dots, 23\}$ |
| $Q$ | capacity of a truck | units |
| $q_i$ | demand of customer $i$ | units |
| $e_i$, $l_i$ | opening and closing of the window of $i$ (service must start in it) | min after midnight |
| $e_0$, $l_0$ | start and end of the working day | min |
| $s_i$ | service time at $i$ | min |
| $c_{ij}$ | travel time $i \to j$ on empty roads | min |
| $\rho_h$ | traffic intensity of hour $h$ | $\ge 1$ |
| $c_{ij}^h = \rho_h c_{ij}$ | travel time $i \to j$ when leaving during hour $h$ | min |
| $M$ | big number that switches a constraint off (2880, two days) | min |
| $x_{ij}^k$ | 1 if truck $k$ drives directly from $i$ to $j$ | $\{0, 1\}$ |
| $y_{ih}$, $y_{0h}^k$ | 1 if the truck leaves customer $i$ (the depot, truck $k$) during hour $h$ | $\{0, 1\}$ |
| $t_0^k$, $t_{n+1}^k$ | departure from and return to the depot of truck $k$ | min |
| $a_i$, $w_i$, $t_i$ | arrival, waiting, service start at customer $i$ | min |
| $z$ | total route duration (objective) | min |
| $B$ | bound of the decision version ([complexity](./complexity.md)) | min |
| $x_{ij}$, $u_i$, $f_{ij}$ | two-index arc variable, MTZ load, load on board ([ILP model](./ilp-model.md)) | binary, units |
| $S$, $q(S)$ | a set of customers, its total demand (capacity cuts) | set, units |
| $z^*$, $z_{LP}$ | best integer value, LP relaxation value | same unit as $z$ |

**Metaheuristics**

| Symbol | Meaning |
| --- | --- |
| $\alpha$ | GRASP greediness: 0 picks the best candidate, 1 a random one |
| $c_1(u)$, $c_2(u)$ | cheapest and second cheapest insertion cost of customer $u$ |
| regret | $c_1 - (c_2 - c_1)$: low when $u$ has one clearly best place |
| RCL | restricted candidate list, the customers whose score is within $\alpha$ of the best |
| $s_{\min}$, $s_{\max}$ | best and worst score of the unrouted customers |
| $A_k$, $Z_k$ | earliest and latest feasible service start at position $k$ of a route |
| kicks | perturbations per GRASP iteration (remove 10 to 20 % of the customers, reinsert) |
| $t$ (tenure) | iterations a moved customer stays tabu |
| $T_0$, $T_f$, $f$ | initial and final temperature of SA, $T_0 = \max(1, f \cdot \text{start cost})$ |
| $\tau$ | elapsed fraction of the time limit, from 0 to 1 |

**Experimental study ([results](../experimentation/results.md))**

| Symbol | Meaning |
| --- | --- |
| BKS | best known solution of a benchmark instance, from the literature |
| gap | $100\,(\text{cost} - \text{BKS}) / \text{BKS}$, in % |
| seed | initial value of the random generator; 10 seeds = 10 independent runs |
| std | standard deviation over the runs |
| Friedman $\chi^2$ | test that the algorithms have the same ranks over the instances |
| Wilcoxon $W$ | paired test between two algorithms over the instances |
| $p$, Holm $p$ | probability of a difference this large by chance; corrected for three comparisons |
