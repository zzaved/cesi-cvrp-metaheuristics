---
sidebar_position: 1
title: Glossary
---

# Glossary

Every technical term used in this project, in plain words. Alphabetical.

| Term | Meaning |
| --- | --- |
| **2-opt** | Local search move that removes two edges of a route and reconnects it the other way, which reverses the segment in between. It removes crossings. |
| **ALNS** | Adaptive Large Neighborhood Search. A metaheuristic that repeatedly destroys part of a solution and repairs it, choosing among several destroy and repair operators with probabilities that adapt to their past success. |
| **Best known solution (BKS)** | The lowest cost ever reported for a benchmark instance. Not always proven optimal. |
| **Big-M** | A large constant used to switch a constraint on or off with a binary variable, for example "if truck goes from i to j, then j starts after i finishes". |
| **Capacity (Q)** | The maximum load a truck can carry. The sum of demands on a route cannot exceed it. |
| **Cross-exchange** | Move that swaps two segments (sequences of consecutive customers) between two routes. |
| **CVRP** | Capacitated Vehicle Routing Problem. Find routes from a depot that serve every customer once with trucks of limited capacity, minimizing total cost. Our Level B. |
| **CVRPTW** | CVRP with Time Windows. Each customer must be served inside a time interval. Our Level A. |
| **Depot** | The place every route starts from and returns to. Node 0. |
| **Destroy and repair** | The two halves of an LNS iteration: remove some customers from the solution, then insert them back, hopefully better. |
| **Gap** | Relative distance to the best known solution: 100 times (our cost minus best known) divided by best known, in percent. |
| **Hamiltonian cycle** | A cycle in a graph that visits every node exactly once and returns to the start. |
| **ILP** | Integer Linear Programming. Optimization with a linear objective, linear constraints, and some variables forced to be integers. Solvable exactly, but slow on large instances. |
| **Local search** | Improving a solution by repeatedly applying small changes (moves) while they reduce the cost. |
| **Lower bound** | A value no solution can beat. Proves how far a solution can be from optimal. |
| **LP relaxation** | The ILP with integrality dropped. Fast to solve and gives a lower bound. |
| **Metaheuristic** | A general strategy to guide heuristics out of local optima. Gives good solutions fast, without proof of optimality. |
| **MTZ constraints** | Miller, Tucker and Zemlin constraints. Use an auxiliary variable per node (here the load) that must increase along each route, which forbids subtours. |
| **Neighborhood** | All the solutions reachable from the current one with one move of a given type. |
| **NP-hard** | At least as hard as every problem in NP. No polynomial algorithm is known for any NP-hard problem, and none exists unless P = NP. |
| **Or-opt** | Move that takes a chain of 1 to 3 consecutive customers and inserts it elsewhere. |
| **Reduction** | A polynomial transformation of every instance of problem A into an instance of problem B with the same answer. If A is hard and A reduces to B, B is hard. |
| **Relocate** | Move that takes one customer out of its position and inserts it somewhere else, in the same route or another. |
| **Route** | The sequence of customers one truck visits, starting and ending at the depot. |
| **Service time** | How long the truck stays at a customer to deliver. |
| **Simulated annealing (SA)** | Metaheuristic that accepts a worse solution with a probability that decreases over time (the temperature cools), which lets the search escape local optima early and settle later. |
| **Swap** | Move that exchanges the positions of two customers. |
| **Tabu search** | Metaheuristic that forbids recently made moves for some iterations (the tabu list) to avoid cycling back. |
| **Time window** | The interval [e, l] in which service at a customer must start. |
| **TSP** | Traveling Salesman Problem. Find the shortest Hamiltonian cycle. The CVRP with one truck and unlimited capacity. |
| **VRPLIB** | The standard file format for vehicle routing instances, and the Python library `vrplib` that reads it. |
| **Waiting time** | Time a truck spends at a customer between arriving early and the opening of the time window. |
