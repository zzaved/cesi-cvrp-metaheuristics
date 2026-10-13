---
sidebar_position: 1
title: Deliverables and grading
---

# Deliverables and grading

What we hand in, when, and how it is evaluated. Dates are tracked in the
[Schedule](../management/schedule.md); progress in the [Checklist](./checklist.md).

## 1. Modeling deliverable (checked, not graded)

**Due:** during Prosit 3. **File:** `notebooks/01_modeling_check.ipynb`. **Owner:** Person 1.

Jupyter Notebook containing:

- context
- formal representation of the data
- problem and objective
- additional constraints chosen
- complexity proof (reduction to an NP-hard or NP-complete problem, for example from TSP or
  Hamiltonian cycle)
- first ILP: decision variables, objective, all constraints
- bibliographic references

**No solution methods yet.** Validated with the tutor on: relevance of the formalization,
validity of the complexity proof, consistency of the ILP.

## 2. Final project deliverable (graded)

**Due:** the day before the presentation. **File:** `notebooks/02_final_deliverable.ipynb`
(plus `03_experimental_study.ipynb`). **Owner:** everyone, by section.

| Part | Content | Owner |
| --- | --- | --- |
| Data formalization | corrected after the modeling check | Person 1 |
| Complexity proof | corrected | Person 1 |
| Complete ILP | corrected, CVRP and CVRPTW | Person 1 |
| Exact approach applications | direct solution, benchmark, lower and upper bounds | Person 1 |
| Chosen metaheuristic | solution encoding, neighborhood structure, operators, guidance mechanisms | Person 2 |
| Implementation | initialization, iterations, termination criteria, internal mechanisms, test cases, demo on several instances | Person 2 |
| Experimental study | structured design, results tables, metrics, behavior analysis, limitations, improvements | Person 3 |

Methodology and statistics must be rigorously justified.

## 3. Presentation (graded)

**When:** last day of the course. **Owner:** everyone; deck by Person 3.

- results oriented
- live code execution on small cases
- context and objectives first
- transparency about challenges
- completed, ongoing and upcoming steps, with a schedule

Plan: [Presentation plan](./presentation-plan.md).

## Grading criteria

| Criterion | What it means for us |
| --- | --- |
| **Quality of solutions** | Gap to best known. **A gap above 7 to 10 percent caps the grade at B.** |
| **Computation time** | Report it, and how it scales with n |
| **Quality of the experimental analysis** | Design, metrics and tests justified |
| **Relevance of conclusions** | Conclusions follow from the data |

Recommendations from the brief: interpret the results, state strengths and limitations, suggest
improvements.
