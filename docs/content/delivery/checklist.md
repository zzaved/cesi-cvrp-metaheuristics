---
sidebar_position: 2
title: Checklist
---

# Checklist

Every requirement of the brief, with its owner. Tick a box only when the item is **done and
reviewed** (merged into `main` and checked by someone from another lane). The README roadmap
mirrors this list.

## Requirements

- [x] Mathematical model (ILP), with traffic, solved by `solve_tdvrptw` (Pablo)
- [x] Three metaheuristics from the course list: Tabu Search (Pablo), SA (Dag), GRASP-ILS (Farida)
- [x] One method chosen from the data: GRASP-ILS
- [x] At least 20 instances with best known values: 56 Solomon CVRPTW instances
- [x] Gap formula applied everywhere: gap(%) = 100 * (cost_ours - cost_best_known) / cost_best_known
- [x] Statistics: Friedman, Wilcoxon with Holm, 10 seeds, same 20 s budget
- [x] Analysis by class (clustered, random, mixed; short and long horizon)
- [x] Level A: CVRPTW; Level B: CVRP (exact study)
- [ ] Scaling beyond 100 customers (limitation)

## Deliverables

- [x] Modeling notebook validated by the tutor (Pablo)
- [x] Final notebook complete, every section filled (`notebooks/02_final_deliverable.ipynb`)
- [ ] Final notebook reviewed by the three of us
- [ ] Presentation deck and live demo rehearsed (all)

## Quality gates

- [x] Every reported solution feasible (1500 of 1500 benchmark runs)
- [x] Mean gap below 7 % on the Solomon test set (GRASP-ILS 1.16 %)
- [x] ruff and pytest green
- [ ] Every bibliography entry verified
