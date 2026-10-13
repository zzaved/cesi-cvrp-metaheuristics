---
sidebar_position: 3
title: Results
---

# Results

Owner: **Person 3**. Template to fill from `results/summary.csv` and `results/summary_tests.csv`
after the campaign (P3-07, P3-08). Every table and figure gets one sentence of interpretation.

:::caution[No results yet]
Numbers below are placeholders. The scaffold's smoke runs on synthetic instances are not results.

:::

## Table 1: quality on CVRP instances

| Instance | n | Best known | NN | NN + LS | SA mean | ALNS best | ALNS mean | ALNS std | ALNS gap (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P-n16-k8 | 15 | | | | | | | | |
| A-n32-k5 | 31 | | | | | | | | |
| ... | | | | | | | | | |
| X-n1001-k43 | 1000 | | | | | | | | |
| **Mean** | | | | | | | | | |

*Interpretation:* _to write._

## Table 2: quality on CVRPTW instances

| Instance | n | Best known (vehicles, distance) | NN | ALNS best | ALNS mean | Gap (%) | Feasible |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C101 | 100 | | | | | | |
| ... | | | | | | | |

## Table 3: exact approach (Person 1)

| Instance | n | ILP status | ILP value | Lower bound | Time (s) | ALNS value | ALNS gap to ILP (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tiny | 6 | | | | | | |
| P-n16-k8 | 15 | | | | | | |

## Table 4: statistical tests

| Test | Algorithms | Statistic | p-value | Holm adjusted | Conclusion |
| --- | --- | --- | --- | --- | --- |
| Friedman | NN, NN+LS, SA, ALNS | | | | |
| Wilcoxon | ALNS vs SA | | | | |

## Figures

| # | Figure | File |
| --- | --- | --- |
| 1 | Gap boxplot per family (A, B, P, X, Solomon) | `results/gap_by_family.png` |
| 2 | Time against n, log-log, with fitted exponent | `results/time_vs_n.png` |
| 3 | Convergence: best and current cost against iteration | notebook 03 |
| 4 | Operator weights over time | notebook 03 |
| 5 | Routes of a solved instance (before and after ALNS) | notebook 02 |

## Findings

1. RQ1: _to write._
2. RQ2: _to write._
3. RQ3: _to write._
4. RQ4: _to write._
5. RQ5: _to write._
