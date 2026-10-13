---
sidebar_position: 2
title: Exploration sheet
---

# Exploration sheet

The sheet produced in class during the prosit exploration phase. The first five sections are kept
**verbatim**; only the last one (hypotheses review) is ours to complete.

## Key words

global warming, Kyoto protocol, greenhouse gases, Paris agreement, ADEME, Smart Multimodal
Mobility, optimizing resource management, delivery route management, minimizes the route,
Operations Research, high modularity, PEP guideline.

## Context

cesiCDP answers the ADEME call for a proposal on smart, low emission mobility by optimizing
delivery routes.

## Problem statement

How can we minimize the total duration of the delivery route using a well-structured algorithm
with the lowest complexity possible?

## Constraints

- visit all clients only once (if possible)
- duration and distance
- fuel or electricity
- topology
- truck size and capacity
- time windows
- lowest complexity
- emergencies
- accuracy
- optimal solution
- use Python
- size of the problem
- test the algorithm on at least 20 different instances

## Hypotheses from class

1. NP problem
2. polynomial complexity
3. can be solved using linear programming
4. the cycle is a Hamiltonian cycle

## Hypotheses review

To be completed as the work progresses: each hypothesis ends **confirmed**, **refuted** or
**refined**, with a pointer to the evidence.

:::caution[Expected outcome, still a hypothesis]
The lines below are what we expect to find. They are **not results** until the linked page
proves them.

:::

| # | Hypothesis | Expected outcome | Evidence (to fill) | Status |
| --- | --- | --- | --- | --- |
| 1 | NP problem | **Refined:** the decision version is NP-complete and the optimization problem is NP-hard, because it generalizes the TSP, which asks for a Hamiltonian cycle of minimum cost. | [Complexity](../technical/complexity.md) | to verify |
| 2 | Polynomial complexity | **Expected refuted:** no polynomial algorithm is known (none exists unless P = NP). Our heuristics run in polynomial time per iteration but give no optimality guarantee. | [Complexity](../technical/complexity.md), time scaling in [Results](../experimentation/results.md) | to verify |
| 3 | Can be solved using linear programming | **Refined:** integer linear programming, not plain LP. ILP gives exact solutions only for small instances; large instances need metaheuristics. The LP relaxation gives a lower bound. | [ILP model](../technical/ilp-model.md), exact study in notebook 02 | to verify |
| 4 | The cycle is a Hamiltonian cycle | **Refined:** with one truck and unlimited capacity, the route is a Hamiltonian cycle (TSP). With k trucks, the solution is k cycles through the depot that together cover every customer once. | [Modeling](../technical/modeling.md) | to verify |
