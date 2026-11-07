---
sidebar_position: 3
title: Results
---

# Results

Owner: **Person 3**. Template to fill from `results/summary.csv` and `results/summary_tests.csv`
after the campaign (P3-07, P3-08). Every table and figure gets one sentence of interpretation.

:::caution[No results yet]
Tables 1 to 3 below are placeholders. The scaffold's smoke runs on synthetic instances are not results.

:::

## Tabu Search on the Solomon CVRPTW instances (7 November 2026)

**Question.** How close does the Tabu Search get to the best known solution (BKS) of the Solomon
instances in a fixed time?

**Protocol.** Code: `src/cvrp/tabu.py`, `experiments/solomon_study.py`,
`experiments/solomon_report.py`.

| Item | Value |
| --- | --- |
| Instances | 56 Solomon instances (PyVRP/VRPLIB copy), n = 100, capacity and time windows |
| Tuning set | C101, C201, R101, R201, RC101, RC201 (one per class), 2 seeds |
| Test set | the other 50 instances, 10 seeds each, 500 runs |
| Objective | total distance, travel time = distance, distances truncated to one decimal (the convention of the BKS files) |
| Gap | $100\,(\text{cost} - \text{BKS}) / \text{BKS}$ |
| Start | time-oriented nearest neighbor (Solomon, 1987) |
| Moves | relocate, swap, 2-opt*, 2-opt, restricted to the 15 nearest neighbors of a customer |
| Guidance | a moved customer is tabu for a tenure drawn in [tenure / 2, 3 tenure / 2]; aspiration if a tabu move gives a new best |
| Budget | 20 s per run |
| Hardware | Apple M2, 7 runs in parallel, Python 3.13 |

Every one of the 500 runs is feasible (each customer served once, capacity and windows respected).
Other algorithms can be added to `ALGORITHMS` in `experiments/solomon_study.py` and run on the same
instances, objective, seeds and time limit.

**Parameters.** Chosen on the tuning set by the lowest mean gap.

| Tenure | Candidates per iteration | Tuning gap (%) |
| --- | --- | --- |
| **20** | **200** | **2.08** |
| 10 | 200 | 2.67 |
| 5 | 200 | 2.88 |
| 5 | 50 | 3.40 |
| 10 | 50 | 5.13 |
| 10 | 500 | 7.05 |
| 20 | 500 | 7.45 |
| 5 | 500 | 7.78 |
| 20 | 50 | 10.15 |

*Interpretation:* 200 candidates balance the quality of each step against the number of steps; the
chosen tenure lies at the edge of the grid, so a longer tenure could still help.

### Table T1: overall (50 instances, 10 seeds)

| Mean gap (%) | Std (%) | Best (%) | Worst (%) | Runs at BKS | Mean routes | Iterations per run |
| --- | --- | --- | --- | --- | --- | --- |
| **4.64** | 3.53 | 0.00 | 15.94 | 108 / 500 | 9.2 | 12 232 |

*Interpretation:* the mean gap is below the 7 % threshold, and one run in five reaches the BKS.

### Table T2: by class

| Class | Routes | Mean gap (%) | Iterations per run | Mean routes |
| --- | --- | --- | --- | --- |
| C1 | short | **0.86** | 17 893 | 10.0 |
| C2 | long | 1.69 | 16 033 | 3.2 |
| R1 | short | 3.87 | 15 210 | 13.6 |
| R2 | long | 6.69 | 9 041 | 6.0 |
| RC1 | short | 7.02 | 7 784 | 13.9 |
| RC2 | long | 7.83 | 6 285 | 7.1 |

*Interpretation:* the gap grows as the number of iterations falls: each of the 200 candidates
re-evaluates whole routes, so long routes (type 2) and the mixed RC classes get fewer iterations in
20 s. RC1 and RC2 are just above 7 %.

**Next improvement:** O(1) feasibility checks with forward time slack
(`timewindows.forward_time_slack`) would multiply the iterations, which is where the gap comes from.

<details>
<summary>Table T3: per instance (10 seeds)</summary>

| Instance   |    BKS |   Mean gap (%) |   Std (%) |   Best gap (%) |   Mean routes |
|:-----------|-------:|---------------:|----------:|---------------:|--------------:|
| C102       |  827.3 |           0.81 |      1.44 |           0    |          10   |
| C103       |  826.3 |           3.91 |      2.77 |           1.1  |          10.2 |
| C104       |  822.9 |           2.14 |      1.63 |           0.46 |          10   |
| C105       |  827.3 |           0    |      0    |           0    |          10   |
| C106       |  827.3 |           0    |      0    |           0    |          10   |
| C107       |  827.3 |           0    |      0    |           0    |          10   |
| C108       |  827.3 |           0    |      0    |           0    |          10   |
| C109       |  827.3 |           0    |      0    |           0    |          10   |
| C202       |  589.1 |           0    |      0    |           0    |           3   |
| C203       |  588.7 |           3.65 |      4.75 |           0    |           3.4 |
| C204       |  588.1 |           6.8  |      3.78 |           0.56 |           3.6 |
| C205       |  586.4 |           0.91 |      1.92 |           0    |           3.2 |
| C206       |  586   |           0    |      0    |           0    |           3   |
| C207       |  585.8 |           0.46 |      1.46 |           0    |           3.1 |
| C208       |  585.8 |           0    |      0    |           0    |           3   |
| R102       | 1466.6 |           2.49 |      1.04 |           1.02 |          19.4 |
| R103       | 1208.7 |           2.41 |      0.65 |           1.16 |          15.8 |
| R104       |  971.5 |           5.02 |      2.63 |           1.65 |          12.6 |
| R105       | 1355.3 |           2.11 |      0.56 |           1.48 |          15.5 |
| R106       | 1234.6 |           3.54 |      0.59 |           2.68 |          13.8 |
| R107       | 1064.6 |           5.19 |      1.18 |           2.69 |          12.5 |
| R108       |  932.1 |           4.98 |      1.6  |           1.89 |          11.1 |
| R109       | 1146.9 |           2.62 |      2.16 |           0.57 |          13.2 |
| R110       | 1068   |           5.23 |      1.09 |           3.74 |          12.6 |
| R111       | 1048.7 |           5.64 |      1.58 |           2.37 |          12.7 |
| R112       |  948.6 |           3.39 |      1.75 |           1.97 |          10.7 |
| R202       | 1029.6 |           4.67 |      1.19 |           2.4  |           8.6 |
| R203       |  870.8 |           4.83 |      1.97 |           2.34 |           6.5 |
| R204       |  731.3 |           7.01 |      2.51 |           3.42 |           5.7 |
| R205       |  949.8 |           6.43 |      1.98 |           4.38 |           6.5 |
| R206       |  875.9 |           9.09 |      1.48 |           7.2  |           6.4 |
| R207       |  794   |          10.32 |      2.99 |           6.83 |           5.3 |
| R208       |  701   |           4.98 |      1.08 |           2.42 |           3.7 |
| R209       |  854.8 |           5.8  |      2.34 |           2.52 |           6.2 |
| R210       |  900.5 |           7.04 |      2.14 |           3    |           6.8 |
| R211       |  746.7 |           6.7  |      2.62 |           4.12 |           4.6 |
| RC102      | 1457.4 |           6.21 |      1.2  |           4.72 |          16.1 |
| RC103      | 1258   |           8.7  |      1.31 |           6.85 |          13.5 |
| RC104      | 1132.3 |           7.55 |      2.16 |           4.39 |          11.8 |
| RC105      | 1513.7 |           4.86 |      1.49 |           3.13 |          16.5 |
| RC106      | 1372.7 |           5.32 |      1.55 |           3.32 |          14.6 |
| RC107      | 1207.8 |           7.92 |      1.84 |           5.06 |          12.8 |
| RC108      | 1114.2 |           8.6  |      2.04 |           3.44 |          12   |
| RC202      | 1092.3 |           8.06 |      1.73 |           5.39 |           9.2 |
| RC203      |  923.7 |           7.54 |      1.75 |           5.53 |           6.7 |
| RC204      |  783.5 |           6.17 |      1.47 |           4.03 |           5.4 |
| RC205      | 1154   |           6.72 |      2.21 |           4.29 |           9.5 |
| RC206      | 1051.1 |           8.44 |      2.97 |           4.07 |           6.7 |
| RC207      |  962.9 |           8.83 |      1.75 |           5.63 |           7.5 |
| RC208      |  776.1 |           9.04 |      2.88 |           5.31 |           4.8 |


</details>


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
