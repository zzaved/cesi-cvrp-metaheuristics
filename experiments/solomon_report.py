"""Summarize results/solomon_benchmark.csv as Markdown tables.

With two or more algorithms in the CSV it also runs the paired tests on the per-instance mean gap
(Friedman, then Wilcoxon signed rank for each pair).

Usage:
    python experiments/solomon_report.py
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Print the overall, per-class and per-instance tables, and the tests if any."""
    b = pd.read_csv(ROOT / "results" / "solomon_benchmark.csv")
    assert b.feasible.all(), "an infeasible run would not be a result"
    b["cls"] = b.instance.str.extract(r"^([A-Z]+\d)")[0]

    overall = b.groupby("algorithm").agg(
        mean_gap=("gap", "mean"),
        std_gap=("gap", "std"),
        best_gap=("gap", "min"),
        worst_gap=("gap", "max"),
        runs_at_bks=("gap", lambda g: int((g <= 1e-6).sum())),
        runs=("gap", "size"),
        mean_routes=("routes", "mean"),
        mean_iterations=("iterations", "mean"),
    )
    print("## Overall\n")
    print(overall.round(2).to_markdown())

    by_cls = b.groupby(["cls", "algorithm"]).agg(
        mean_gap=("gap", "mean"), iterations=("iterations", "mean"), routes=("routes", "mean")
    )
    print("\n## By class\n")
    print(by_cls.round(2).to_markdown())

    per_inst = b.groupby(["instance", "algorithm"]).gap.agg(["mean", "min"]).unstack()
    print("\n## Per instance (gap %, mean and best over the seeds)\n")
    print(per_inst.round(2).to_markdown())

    algos = sorted(b.algorithm.unique())
    if len(algos) < 2:
        return
    means = b.groupby(["instance", "algorithm"]).gap.mean().unstack()
    print("\n## Tests on the per-instance mean gap\n")
    if len(algos) > 2:
        stat, p = friedmanchisquare(*(means[a] for a in algos))
        print(f"- Friedman: chi2 = {stat:.1f}, p = {p:.2g}")
    for a, c in itertools.combinations(algos, 2):
        stat, p = wilcoxon(means[a], means[c])
        print(f"- Wilcoxon {a} vs {c}: W = {stat:.0f}, p = {p:.2g}")


if __name__ == "__main__":
    main()
