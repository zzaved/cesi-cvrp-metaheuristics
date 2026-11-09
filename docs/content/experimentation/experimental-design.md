---
sidebar_position: 2
title: Experimental design
---

# Experimental design

Same protocol as section 8 of the final notebook (`notebooks/02_final_deliverable.ipynb`); results on the
[Results](./results.md) page.

**Questions.** Which metaheuristic gives the lowest gap to the best known solution at equal time?
Is the difference significant, and does it hold on every family of instances?

| Item | Value |
| --- | --- |
| Instances | the 56 Solomon CVRPTW instances, 100 customers (C1, C2, R1, R2, RC1, RC2) |
| Distances | Euclidean, truncated to one decimal, the convention of the best known values (checked on all 56) |
| Objective | total distance, travel time = distance, no traffic ([model](../technical/modeling.md)) |
| Tuning set | C101, C201, R101, R201, RC101, RC201, seeds 101 and 102 |
| Test set | the other 50 instances, seeds 1 to 10: 500 runs per algorithm |
| Budget | 20 s of wall-clock time per run, construction included, the same for every algorithm |
| Machine | one Apple M2 (8 cores), 7 runs in parallel, Python 3.13; the jobs of the three algorithms are interleaved |
| Metric | gap $= 100\,(\text{cost} - \text{BKS}) / \text{BKS}$; GRASP-ILS and SA solutions checked by the shared evaluator, Tabu Search ones by its cost function (capacity, windows, return to the depot), and every solution for coverage and cost |
| Target | the brief caps the grade when the gap exceeds 7 to 10 %; 7 % is the stricter reading |
| Tests | Friedman on the per-instance mean gaps, then Wilcoxon signed rank per pair with Holm correction, 5 % |

`python experiments/solomon_study.py tune`, then `run`, writes the two CSV files read below.

## Why these choices

- **Unit of analysis: the instance.** For each (instance, algorithm) the mean gap over the 10 seeds
  is one observation; seeds measure robustness, instances are the independent samples.
- **Non-parametric tests.** Gaps are not normally distributed (many zeros on C instances), so
  Friedman (three algorithms, ranks per instance) and then Wilcoxon signed rank per pair, with the
  Holm correction for three comparisons (Demsar, 2006).
- **Equal wall-clock time** rather than equal iterations: one iteration means very different work
  for the three methods (a move for SA, 200 sampled moves for Tabu Search, a full construction,
  descent and 90 kicks for GRASP-ILS).
- **Tuning set disjoint from the test set**, with different seeds, so no test instance chooses a
  parameter.
- **Distances truncated to one decimal**, the convention under which the 56 BKS values were
  computed (checked on every file); exact distances inflate every gap by about 0.3 %.

## Threats to validity

- SA is compiled (numba), Tabu Search and GRASP-ILS are pure Python: equal time mixes algorithm
  and implementation.
- The M2 has performance and efficiency cores; jobs are interleaved to spread the effect.
- All instances have 100 customers; scaling is not measured.
- The benchmark objective is distance without traffic (no published values exist with traffic).
