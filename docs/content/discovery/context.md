---
sidebar_position: 1
title: Context
---

# Context

## The call

**ADEME** (Agence de l'Environnement et de la Maitrise de l'Energie, the French Environment and
Energy Management Agency) has launched a call for pilot projects on **Smart Multimodal Mobility**:
new mobility solutions that use less energy and emit less, for people and for goods.

**CesiCDP**, our fictional organization, already works on smart mobility and answers the call on
one theme: **delivery route management**. The submission is due in **five weeks**.

## Why routes matter for the climate

- The **Kyoto Protocol** (signed 1997, in force 2005) committed industrialized countries to cut
  greenhouse gas emissions.
- The **Paris Agreement** (2015) set the goal of keeping warming well below 2 degrees Celsius,
  with national reduction plans.
- Transport is one of the largest emitting sectors in France, and road freight is a large share of
  it (exact share to cite from CITEPA or ADEME, *to verify*).

Better logistics is a direct lever: the same deliveries done with fewer kilometres and fewer
trucks mean less fuel or electricity and fewer emissions. The same algorithms apply to mail
delivery, parcel and product delivery, road network management and waste collection.

## What CesiCDP proposes

Compute, on a road network, routes that connect a subset of cities (customers) and return to the
starting point (the depot), so that the **total duration** of the routes is minimal. The base
problem is enriched with constraints that make it realistic: vehicle capacity first, then delivery
time windows. The brief also mentions traffic varying by time slot; we treat it as an extension
(see [Problem mapping](./problem-mapping.md#5-scope)).

| Scope | Problem | Status |
| --- | --- | --- |
| **Level B (expected)** | CVRP: k trucks with identical capacity | committed |
| **Level A (advanced)** | CVRPTW: capacity plus a time window per customer, waiting allowed | planned |

## What the client expects

The work follows the path an operations research team would take:

1. **Formal modeling** of the problem.
2. **Algorithmic design and implementation** of a solution method.
3. **Experimental study** of the method's behavior and performance.
4. **Presentation** of the results to the team, in English.

Each step is a Jupyter Notebook, with **storytelling** given priority: the reader must follow the
reasoning, not only the code. Code must be readable, well commented, performance oriented and
follow PEP 8; high modularity is not required.

## The team

The brief describes a team of four. **We are three: Pablo, Dag and Farida.** The four meeting
roles (facilitator, secretary, scribe, manager) are therefore combined, see
[Working agreements](../management/working-agreements.md).
