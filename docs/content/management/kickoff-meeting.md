---
sidebar_position: 1
title: Kickoff meeting
---

# Kickoff meeting

**Tuesday 13 October 2026, afternoon.** Pablo, Dag, Farida. Goal: leave the room with every lane
assigned, the open decisions closed, and everyone knowing their first task.

## Before the meeting (10 minutes each)

- Read [Start here](../intro.md), [Task separation](../task-separation.md) and
  [Problem mapping](../discovery/problem-mapping.md).
- Clone the repository and run `make install && make test` (21 tests should pass).
- Think about which lane you prefer and why.

## Agenda (60 minutes)

| Time | Item | Output |
| --- | --- | --- |
| 0:00 | Pick the facilitator, secretary and scribe for this meeting | roles |
| 0:05 | Walk through the problem mapping: agree on scope (Level B committed, Level A planned) | scope agreed |
| 0:15 | Walk through the repository: what runs, where the TODOs are | shared picture |
| 0:25 | **Assign lanes**: Person 1, Person 2, Person 3 | names in the task separation table |
| 0:35 | Close the open decisions below | decisions table filled |
| 0:50 | Confirm dates with the tutor's calendar; first task per person | schedule updated |
| 0:55 | Next meeting date and roles rotation | calendar invite |

## Decisions to make

| # | Decision | Options | Proposal | Decided |
| --- | --- | --- | --- | --- |
| D1 | Who takes which lane | Pablo, Dag, Farida | by preference and strengths | |
| D2 | Metaheuristic | ALNS + SA, tabu, GA | ALNS + SA, SA as baseline | |
| D3 | ILP solver | PuLP with CBC, OR-Tools | PuLP with CBC (already a dependency) | |
| D4 | Fleet size | fixed from instance, free | fixed for CVRPLIB (`-k`), free for synthetic | |
| D5 | Objective at Level A | travel time only, travel plus waiting | travel time only (Solomon convention) | |
| D6 | Instance list | see [Instances](../experimentation/instances.md) | the 26 proposed | |
| D7 | Time budget per run | fixed, proportional to n | $\min(0.12\,n, 300)$ s | |
| D8 | Weekly meeting slot | | | |
| D9 | Exact dates: modeling check, final deliverable, presentation | | see [Schedule](./schedule.md) | |
| D10 | Communication channel and response time | | | |

## First task per lane (this week)

| Lane | First task |
| --- | --- |
| Person 1 | P1-01 notation table and P1-03 proof draft |
| Person 2 | P2-01 freeze the API with Person 3, then P2-02 swap |
| Person 3 | P3-01 download instances, P3-02 instance list |

## Minutes

*Scribe fills this during the meeting.*

- Present:
- Roles:
- Decisions: see table above
- Actions:
- Next meeting:
