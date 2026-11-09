---
sidebar_position: 4
title: Metaheuristic
---

# Metaheuristics

Same text as section 5 of the final notebook (`notebooks/02_final_deliverable.ipynb`). Implementation details of GRASP-ILS:
`notebooks/04_grasp.ipynb` (Farida); of SA: `notebooks/SA.ipynb` (Dag); of Tabu Search:
`src/cvrp/tabu.py` (Pablo).

## Choice of the method

Three metaheuristics from the course list were implemented on the same instance, solution and
evaluator code and compared under one protocol ([Results](../experimentation/results.md)): **Tabu Search** (Pablo,
`src/cvrp/tabu.py`), **Simulated Annealing** (Dag, `src/cvrp/sa.py`, compiled with numba) and
**GRASP** with an iterated local search inside each iteration (Farida, `src/cvrp/grasp.py`). The
rule fixed before the campaign was: feasible on every run, then lowest mean gap, then lowest mean
time. GRASP-ILS is feasible on all 500 test runs and has the lowest mean gap (1.16 %, against
1.70 % for SA and 3.98 % for Tabu Search), with every pairwise difference significant: it is the
chosen method. Its full study is `notebooks/04_grasp.ipynb`.

| Component | GRASP-ILS |
| --- | --- |
| Encoding | a list of routes, each a list of customers; the depot is implicit at both ends |
| Initialization | randomized adaptive parallel insertion: each unrouted customer keeps its cheapest feasible insertion per route; score = regret $c_1 - (c_2 - c_1)$; a customer is drawn from the restricted candidate list $\{u : \text{score}(u) \le s_{\min} + \alpha (s_{\max} - s_{\min})\}$; a new route starts from a customer far from the depot or with an early due time; if more than $K$ routes are opened, the smallest ones are emptied and reinserted |
| Neighborhoods | relocate, swap, 2-opt*, Or-opt (chains of 2 or 3), cross-exchange (segments up to 2), 2-opt; only between a customer and its 20 nearest customers (granular) |
| Local search | variable neighborhood descent: after any improvement restart from the first neighborhood; first improvement |
| Time windows | each route stores the earliest start $A_k$ and the latest feasible start $Z_k$ of every position (Savelsbergh, 1992), so a move is checked in $O(1)$ plus the moved segment; intra-route 2-opt re-checks the route |
| Guidance | multi-start (diversification) by the randomized construction; intensification by 90 kicks per iteration: remove a cluster of 10 to 20 % of the customers, reinsert them at their cheapest place, descend, keep only if shorter |
| Acceptance | a solution replaces the best only if it is feasible for the shared evaluator and shorter |
| Stopping criterion | wall-clock time limit (20 s in the benchmark), checked between iterations and kicks |
| Parameters | $\alpha = 0.3$, first improvement, 90 kicks: the best of 12 settings on the 6 tuning instances ([Results](../experimentation/results.md)) |
| Objective | a parameter: total distance (benchmark) or total route duration with hourly traffic, the objective of the [model](./modeling.md) (`objective="duration"`) |

The two other algorithms, for the comparison of the [results](../experimentation/results.md):

| Component | Tabu Search | Simulated Annealing |
| --- | --- | --- |
| Encoding | list of routes | list of routes (arrays, compiled with numba) |
| Initialization | time-oriented nearest neighbor (Solomon, 1987) | randomized cheapest feasible insertion |
| Neighborhood | relocate, swap, 2-opt*, 2-opt between a customer and one of its 15 nearest | relocate a customer or a chain of 2 or 3, swap, 2-opt, 2-opt*, between random routes |
| Step | best non-tabu move among 200 sampled | one random feasible move |
| Guidance | a moved customer is tabu for a tenure drawn in $[t/2, 3t/2]$; aspiration if a tabu move gives a new best | Metropolis acceptance, $T(\tau) = T_0 (T_f / T_0)^{\tau}$, $\tau$ = elapsed fraction of the time limit, $T_0 = \max(1, f \cdot \text{start cost})$ |
| Stopping | time limit | time limit |
| Tuned | tenure $t = 20$, 200 candidates (grid of 9) | $f = 0.005$, $T_f = 0.005$ (grid of 12) |
| Fixed | 15 nearest neighbors | move probabilities (uniform) |
