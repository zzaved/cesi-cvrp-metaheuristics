---
sidebar_position: 3
title: Presentation plan
---

# Presentation plan

Owner: **Person 3** (deck), everyone presents. In English, results oriented, with live code on a
small case. Target length: **20 minutes plus questions** (*to confirm*).

## Outline

| # | Section | Content | Speaker | Minutes |
| --- | --- | --- | --- | --- |
| 1 | Context and objectives | ADEME call, why routes matter, CVRP and CVRPTW, success criteria | Person 1 | 2 |
| 2 | Model | Graph, variables, objective, constraints; one slide per level | Person 1 | 3 |
| 3 | Why it is hard | Reduction chain HC to TSP to CVRP; consequence for the method | Person 1 | 2 |
| 4 | Our method | ALNS loop diagram, operators, acceptance, adaptive weights | Person 2 | 3 |
| 5 | **Live demo** | Notebook 02 demo cell: small instance, before and after, under 1 minute | Person 2 | 2 |
| 6 | Results | Gap table, time scaling, statistical tests, one route map | Person 3 | 4 |
| 7 | Challenges | What did not work and what we learned, honestly | all | 2 |
| 8 | Status and next steps | Done, ongoing, upcoming with schedule | Person 3 | 2 |

## Status slide (keep updated)

| Done | Ongoing | Next |
| --- | --- | --- |
| Repository, solver scaffold, tests, CI, documentation | Lane assignment, modeling notebook | ILP, operators, instance list |

## Demo checklist

- [ ] Runs from a fresh kernel in under 60 seconds
- [ ] Uses an instance already in the repository (synthetic, no download)
- [ ] Shows initial and final routes side by side and the convergence curve
- [ ] Backup: screenshots in the deck if the laptop fails

## Rehearsal

- [ ] Full run through, timed, in week 5
- [ ] Questions we expect: why ALNS, why MTZ, gap on large X instances, statistical test choice
