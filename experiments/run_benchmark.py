"""Run every algorithm on every instance and seed listed in a YAML config.

Usage:
    python experiments/run_benchmark.py --config experiments/config.yaml

Writes one CSV row per run with: instance, family, n, algorithm, seed, cost,
best_known, gap, seconds, routes, feasible.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import yaml

from cvrp import Instance, Solution
from cvrp.alns import ALNSParams, alns
from cvrp.construct import nearest_neighbor
from cvrp.neighborhoods import local_search
from cvrp.utils import gap_percent, timer

ROOT = Path(__file__).resolve().parents[1]


def load_instances(cfg: dict) -> Iterator[tuple[str, Instance]]:
    """Yield (family, instance) pairs; missing files are skipped with a warning."""
    for spec in cfg.get("synthetic", []):
        spec = dict(spec)
        yield f"synthetic-{spec['distribution']}", Instance.random(**spec)
    for fmt in ("vrplib", "solomon"):
        for spec in cfg.get(fmt, []):
            path = ROOT / spec["path"]
            if not path.exists():
                print(
                    f"skipping {path.name}: not downloaded (see data/README.md)", file=sys.stderr
                )
                continue
            sol = spec.get("solution")
            sol_path = ROOT / sol if sol and (ROOT / sol).exists() else None
            inst = Instance.from_vrplib(path, sol_path, instance_format=fmt)
            if spec.get("best_known") is not None:
                inst.best_known = float(spec["best_known"])
            yield fmt, inst


def run_algorithm(name: str, params: dict, inst: Instance, seed: int, limit: float) -> Solution:
    """Dispatch one algorithm by name and return its best solution."""
    if name == "nn":
        return nearest_neighbor(inst)
    if name == "nn_ls":
        return local_search(nearest_neighbor(inst), inst)
    if name == "alns":
        res = alns(inst, ALNSParams(time_limit=limit, **params), seed=seed)
        return local_search(res.best, inst)
    # TODO(Person 2): add "sa" (plain simulated annealing) and ALNS variants.
    raise ValueError(f"unknown algorithm {name!r}")


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the grid and write the CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=ROOT / "experiments" / "config.yaml", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    cfg = yaml.safe_load(args.config.read_text())
    out = args.output or ROOT / cfg.get("output", "results/benchmark.csv")
    rows = []
    for family, inst in load_instances(cfg["instances"]):
        for algo, params in cfg["algorithms"].items():
            seeds = cfg["seeds"] if algo not in {"nn", "nn_ls"} else cfg["seeds"][:1]
            for seed in seeds:
                with timer() as t:
                    sol = run_algorithm(algo, params or {}, inst, seed, cfg["time_limit"])
                cost = sol.cost(inst)
                rows.append(
                    {
                        "instance": inst.name,
                        "family": family,
                        "n": inst.n_customers,
                        "time_windows": inst.has_time_windows,
                        "algorithm": algo,
                        "seed": seed,
                        "cost": cost,
                        "best_known": inst.best_known,
                        "gap": gap_percent(cost, inst.best_known) if inst.best_known else None,
                        "seconds": t["seconds"],
                        "routes": len(sol),
                        "feasible": sol.is_feasible(inst),
                    }
                )
                print(
                    f"{inst.name:<28} {algo:<6} seed={seed:<3} cost={cost:10.1f} "
                    f"t={t['seconds']:6.2f}s"
                )
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
