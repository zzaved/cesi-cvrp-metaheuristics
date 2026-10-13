# cesi-cvrp-metaheuristics

**Shorter delivery routes for the ADEME smart mobility call.** A Python solver for the Capacitated
Vehicle Routing Problem (CVRP) and its time window variant (CVRPTW): formal model, NP-hardness
proof, integer linear program for small instances, an Adaptive Large Neighborhood Search
metaheuristic for realistic sizes, VRPLIB benchmarks and a statistical experimental study.
CESI Ecole d'Ingenieurs, *Algorithms and Combinatorial Optimization*.

![CI](https://github.com/zzaved/cesi-cvrp-metaheuristics/actions/workflows/ci.yml/badge.svg)
![Docs](https://github.com/zzaved/cesi-cvrp-metaheuristics/actions/workflows/docs.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**[Read the documentation](https://zzaved.github.io/cesi-cvrp-metaheuristics/)** ·
[Task separation](docs/content/task-separation.md) ·
[Problem mapping](docs/content/discovery/problem-mapping.md) ·
[Kickoff meeting](docs/content/management/kickoff-meeting.md)

> **Status: scaffold.** The structure, the core data model and a first working ALNS are in place
> so the team can work in parallel. Everything else is marked `TODO(Person N)` in the code and
> tracked in the [checklist](docs/content/delivery/checklist.md).

## Context

CesiCDP (our fictional organization) answers an ADEME call (French Environment and Energy
Management Agency) for pilot projects on Smart Multimodal Mobility. Better logistics is a direct
lever on greenhouse gas emissions, in the spirit of the Kyoto Protocol and the Paris Agreement:
the same deliveries with fewer kilometres use less fuel. We compute routes on a road network that
serve a set of customers and return to the depot, **minimizing total route duration**. Deadline:
five weeks.

| Level | Problem | Constraints |
| --- | --- | --- |
| **B (expected)** | CVRP | k trucks with identical capacity Q; each customer served once |
| **A (advanced)** | CVRPTW | plus a time window per customer; no delivery outside it; waiting allowed |

## Repository map

```
src/cvrp/          the solver package
  instance.py        Instance dataclass, VRPLIB and Solomon loaders, random generator
  solution.py        routes, cost, feasibility checks
  construct.py       nearest neighbor, Clarke and Wright, sweep
  neighborhoods.py   2-opt, relocate, swap, Or-opt, cross-exchange
  alns.py            ALNS: destroy, repair, adaptive weights, SA acceptance
  sa.py              simulated annealing helpers and baseline
  ilp.py             exact models (PuLP) for small instances
  timewindows.py     schedules, waiting, window feasibility
  utils.py, viz.py   distance matrix, timing, gap; plots
tests/             unit tests and the end to end smoke test
experiments/       run_benchmark.py, analyze.py, config.yaml
notebooks/         01 modeling check, 02 final deliverable, 03 experimental study
data/              downloaded instances (not committed, see data/README.md)
results/           benchmark CSVs and figures (not committed)
docs/              Docusaurus documentation site
```

## Quick start

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # or: make install
pytest                           # 21 tests, includes the smoke test
python experiments/run_benchmark.py --config experiments/config.yaml   # or: make benchmark
python experiments/analyze.py --results results                        # or: make analyze
```

Minimal use from Python:

```python
from cvrp import Instance
from cvrp.alns import ALNSParams, alns

inst = Instance.random(100, capacity=150, seed=1, distribution="clustered")
res = alns(inst, ALNSParams(iterations=2000), seed=1)
print(res.best_cost, res.best.is_feasible(inst))
```

Documentation site locally: `make docs` (Node 20+).

## Reproducing results

1. Download the instances listed in `experiments/config.yaml` as described in `data/README.md`.
2. `make benchmark` writes `results/benchmark.csv` (one row per instance, algorithm and seed).
3. `make analyze` writes `results/summary.csv`, `results/summary_tests.csv` and the figures.
4. `notebooks/03_experimental_study.ipynb` turns them into the study.

Seeds, time limits and parameters all live in `config.yaml`; nothing is set by hand.

## Roadmap

Mirrors [docs/content/delivery/checklist.md](docs/content/delivery/checklist.md).

- [ ] Mathematical model (ILP)
- [ ] A metaheuristic (ALNS with SA acceptance; plain SA as baseline)
- [ ] Python solver handling realistic instance sizes (up to several thousand customers for the basic version)
- [ ] At least 20 different instances from different usage scenarios
- [ ] Visualizations and statistics
- [ ] Validation on VRPLIB reference instances with the `vrplib` library
- [ ] Gap formula: gap(%) = 100 * (cost_ours - cost_best_known) / cost_best_known
- [ ] Analysis by instance size, customer distribution, constraints (capacity, time windows)
- [ ] Level B: CVRP
- [ ] Level A: CVRPTW

## Team

| Lane | Person | Name |
| --- | --- | --- |
| Modeling and exact methods | Person 1 | _assigned at kickoff_ |
| Metaheuristic engine | Person 2 | _assigned at kickoff_ |
| Data, experiments and communication | Person 3 | _assigned at kickoff_ |

Pablo, Dag and Farida. See [Task separation](docs/content/task-separation.md) and
[Working agreements](docs/content/management/working-agreements.md).

## License

[MIT](LICENSE).
