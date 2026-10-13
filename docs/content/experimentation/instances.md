---
sidebar_position: 1
title: Instances
---

# Instances

Owner: **Person 3**. Requirement: **at least 20 different instances from different usage
scenarios**. Download instructions: `data/README.md`. Run list: `experiments/config.yaml`.

## Scenarios we must cover

Each scenario changes one factor of the [experimental design](./experimental-design.md):

| Scenario | Factor it tests | Source |
| --- | --- | --- |
| Small, exact optimum reachable | quality against the true optimum | Augerat P, small A, synthetic |
| Random (uniform) customers | baseline behavior | Augerat A, Uchoa X (R), Solomon R |
| Clustered customers | effect of geography | Augerat B, Uchoa X (C), Solomon C |
| Mixed | in between | Solomon RC, Uchoa X (RC) |
| Size from 100 to 1000 | scaling of quality and time | Uchoa X |
| Several thousand customers | realistic size, no best known | synthetic |
| Tight and loose capacity | effect of route count | X instances differ in demand and route size |
| Time windows, short horizon | Level A, many short routes | Solomon type 1 (C1, R1, RC1) |
| Time windows, long horizon | Level A, few long routes | Solomon type 2 (C2, R2, RC2) |

## Proposed list (26 instances)

*Proposal to validate at kickoff; names to verify against CVRPLIB once downloaded.*

| # | Instance | n | Problem | Scenario | Best known from |
| --- | --- | --- | --- | --- | --- |
| 1 | P-n16-k8 | 15 | CVRP | small, ILP optimum | `.sol` |
| 2 | A-n32-k5 | 31 | CVRP | small, random | `.sol` |
| 3 | B-n31-k5 | 30 | CVRP | small, clustered | `.sol` |
| 4 | A-n45-k6 | 44 | CVRP | random | `.sol` |
| 5 | B-n50-k7 | 49 | CVRP | clustered | `.sol` |
| 6 | P-n51-k10 | 50 | CVRP | tight capacity | `.sol` |
| 7 | A-n60-k9 | 59 | CVRP | random | `.sol` |
| 8 | B-n78-k10 | 77 | CVRP | clustered | `.sol` |
| 9 | A-n80-k10 | 79 | CVRP | random | `.sol` |
| 10 | X-n101-k25 | 100 | CVRP | size 100, many short routes | `.sol` |
| 11 | X-n157-k13 | 156 | CVRP | size 150 | `.sol` |
| 12 | X-n204-k19 | 203 | CVRP | size 200 | `.sol` |
| 13 | X-n303-k21 | 302 | CVRP | size 300 | `.sol` |
| 14 | X-n502-k39 | 501 | CVRP | size 500 | `.sol` |
| 15 | X-n801-k40 | 800 | CVRP | size 800 | `.sol` |
| 16 | X-n1001-k43 | 1000 | CVRP | size 1000 | `.sol` |
| 17 | rand-uniform-n2000 | 2000 | CVRP | thousands, uniform | none: compare algorithms |
| 18 | rand-clustered-n2000 | 2000 | CVRP | thousands, clustered | none |
| 19 | rand-uniform-n5000 | 5000 | CVRP | stress test | none |
| 20 | C101 | 100 | CVRPTW | clustered, short horizon | literature, to cite |
| 21 | R101 | 100 | CVRPTW | random, short horizon | literature |
| 22 | RC101 | 100 | CVRPTW | mixed, short horizon | literature |
| 23 | C201 | 100 | CVRPTW | clustered, long horizon | literature |
| 24 | R201 | 100 | CVRPTW | random, long horizon | literature |
| 25 | RC201 | 100 | CVRPTW | mixed, long horizon | literature |
| 26 | C1_2_1 (Homberger) | 200 | CVRPTW | larger TW instance | literature |

A separate **tuning set** (for example A-n33-k5, B-n35-k5, X-n110-k13, R102) is used only for
parameter tuning (P3-06) and never appears in the reported results.

## Notes on best known values

- CVRPLIB `.sol` files give the best known cost under **rounded** Euclidean distances. Our loader
  rounds `EUC_2D` by default, so gaps are comparable.
- Solomon best known values are usually reported with a **hierarchical objective** (fewest
  vehicles first, then distance) and specific rounding. Check which convention each value uses
  before computing a gap, and cite the source.
- Synthetic instances have no best known value: report cost relative to the best of all our runs,
  and compare algorithms with paired tests.
