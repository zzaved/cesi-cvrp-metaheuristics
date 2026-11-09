---
sidebar_position: 0
title: Final notebook guide
---

# Final notebook guide

`notebooks/02_final_deliverable.ipynb` is the graded deliverable: the whole project in one
notebook, with a table of contents at the top and a glossary of every symbol at the end. This page
maps each section to the documentation page that holds the same text, and lists what each of us
should be able to explain.

| Section | Content | Same text in the docs |
| --- | --- | --- |
| 1 | data, traffic matrix, decision variables | [Modeling](../technical/modeling.md) |
| 2 | NP-hardness: Hamiltonian cycle reduces to our problem | [Complexity](../technical/complexity.md) |
| 3 | the complete ILP, read line by line; what the code solves | [Modeling](../technical/modeling.md) |
| 4 | up to which size the ILP proves the optimum | [ILP model](../technical/ilp-model.md) |
| 5 | GRASP-ILS, and Tabu Search and SA for the comparison | [Metaheuristic](../technical/metaheuristic.md) |
| 6, 7 | demo on three instances; tests; check against the ILP optima | [Architecture](../technical/architecture.md) |
| 8 | protocol, tuning, results, statistical tests | [Experimental design](../experimentation/experimental-design.md), [Results](../experimentation/results.md) |
| 9, 10 | limitations, references | [Bibliography](../reference/bibliography.md) |
| A | glossary of symbols | [Modeling](../technical/modeling.md#glossary-of-symbols) |

## The results in four lines

- The problem is NP-hard; the exact ILP proves the optimum up to 7 or 8 customers with traffic and
  up to 100 customers on easy instances without traffic (C101, R101, equal to the best known values).
- Three metaheuristics on 50 Solomon test instances, 10 seeds, 20 s: GRASP-ILS 1.16 %, SA 1.70 %,
  Tabu Search 3.98 % mean gap; all 1500 runs feasible.
- Friedman p = 4e-13; every pair differs after the Holm correction (GRASP-ILS vs SA p = 7.5e-4).
- GRASP-ILS is chosen; it finds every optimum the ILP proves on sub-instances of up to 50 customers.

## What to study before the presentation

1. **The variables** of section 3: $x_{ij}^k$, $y_{ih}$, $t_0^k$, $t_{n+1}^k$, $a_i$, $w_i$, $t_i$, and why the
   depot is split into $0$ and $n + 1$ (the duration of a truck is $t_{n+1}^k - t_0^k$).
2. **Constraint (8)**: how the departure hour picks the travel time $\rho_h c_{ij}$, and what $M$ does.
3. **The reduction** of section 2, both directions.
4. **The gap and the protocol**: why distances are truncated to one decimal, why tuning and test
   instances are disjoint, why equal time.
5. **The tests**: what Friedman, Wilcoxon and Holm say, and why the unit is the instance.
6. **The limitations** of section 9, the first questions the jury will ask.
