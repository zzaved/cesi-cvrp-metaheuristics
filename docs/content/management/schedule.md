---
sidebar_position: 3
title: Schedule
---

# Schedule

Five weeks, from the kickoff on **13 October 2026** to the ADEME submission. Dates of the modeling
check and of the presentation are **assumptions to confirm** at kickoff (D9).

```mermaid
gantt
  title Five week roadmap
  dateFormat YYYY-MM-DD
  axisFormat %d %b
  section Milestones
  Kickoff                         :milestone, m0, 2026-10-13, 0d
  Modeling check (Prosit 3)       :milestone, m1, 2026-10-23, 0d
  Final deliverable               :milestone, m2, 2026-11-12, 0d
  Presentation                    :milestone, m3, 2026-11-13, 0d
  section Person 1
  Model and complexity proof      :p1a, 2026-10-13, 8d
  First ILP                       :p1b, 2026-10-19, 5d
  ILP code and bounds             :p1c, 2026-10-24, 10d
  Savings and sweep               :p1d, 2026-10-28, 7d
  Exact study and CVRPTW ILP      :p1e, 2026-11-02, 8d
  section Person 2
  API freeze and operators        :p2a, 2026-10-13, 10d
  Shaw and regret                 :p2b, 2026-10-19, 6d
  Granular and CVRPTW             :p2c, 2026-10-26, 12d
  Profiling and numba             :p2d, 2026-11-02, 6d
  Final sections and demo         :p2e, 2026-11-05, 7d
  section Person 3
  Instances and list              :p3a, 2026-10-13, 9d
  Design and SA baseline          :p3b, 2026-10-19, 10d
  Tuning                          :p3c, 2026-10-28, 5d
  Campaign and statistics         :p3d, 2026-11-02, 7d
  Results and deck                :p3e, 2026-11-06, 7d
```

## Week by week

| Week | Dates | Goal | Done when |
| --- | --- | --- | --- |
| 1 | 13 to 18 Oct | Lanes assigned; model and proof drafted; API frozen; instances downloaded | kickoff decisions closed; notation and proof drafts reviewed |
| 2 | 19 to 25 Oct | **Modeling deliverable**; new operators; instance list and design final | tutor check passed; 20 plus instances in `config.yaml` |
| 3 | 26 Oct to 1 Nov | ILP running on small n; ALNS complete for CVRP; first gaps on A and X | gap table for A instances in the weekly meeting |
| 4 | 2 to 8 Nov | Scaling and CVRPTW; full campaign; statistics | `results/` complete; notebook 03 draft |
| 5 | 9 to 13 Nov | Final notebook, deck, rehearsal | final deliverable handed in; presentation given |

## Weekly log

*Appended after each weekly meeting by the scribe.*

| Week | Done | Blocked | Decisions |
| --- | --- | --- | --- |
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
