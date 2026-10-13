---
sidebar_position: 2
title: Checklist
---

# Checklist

Every requirement of the brief, with its owner. Tick a box only when the item is **done and
reviewed** (merged into `main` and checked by someone from another lane). The README roadmap
mirrors this list.

## Requirements

- [ ] Mathematical model (ILP) (Person 1)
- [ ] A metaheuristic: ALNS with SA acceptance; plain SA as baseline (Person 2)
- [ ] Python solver handling realistic instance sizes, up to several thousand customers for the basic version (Person 2)
- [ ] At least 20 instances from different usage scenarios (Person 3)
- [ ] Visualizations and statistics (Person 3)
- [ ] Validation on VRPLIB reference instances with the `vrplib` library (Person 3)
- [ ] Gap formula applied everywhere: gap(%) = 100 * (cost_ours - cost_best_known) / cost_best_known (Person 3)
- [ ] Analysis by instance size, customer distribution and constraints (capacity, time windows) (Person 3)
- [ ] Level B: CVRP (Person 2)
- [ ] Level A: CVRPTW (Person 2)

## Deliverables

- [ ] Modeling notebook validated by the tutor (Person 1)
- [ ] Final notebook complete, every section filled (all)
- [ ] Experimental study notebook complete (Person 3)
- [ ] Presentation deck and live demo rehearsed (all)

## Quality gates

- [ ] Every reported solution passes `Solution.violations` (Person 3)
- [ ] Mean gap below 7 percent on VRPLIB CVRP instances (Person 2)
- [ ] CI green on `main`: ruff and pytest (all)
- [ ] Every bibliography entry verified (Person 1)
- [ ] Hypotheses review in the exploration sheet completed (Person 1)
