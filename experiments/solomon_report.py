"""Summarize results/solomon_benchmark.csv as Markdown tables.

With two or more algorithms in the CSV it also runs the paired tests on the per-instance mean gap
(Friedman, then Wilcoxon signed rank for each pair with Holm correction) and applies the team's
selection rule, fixed before the campaign: feasible on every run, then lowest mean gap, then
lowest mean computation time.

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
    feasible = b.groupby("algorithm").feasible.all()
    print("## Feasibility (every run must be feasible)\n")
    print(b.groupby("algorithm").feasible.agg(["sum", "size"]).to_markdown())
    print()
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
        mean_seconds=("seconds", "mean"),
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
    pairs = []
    for a, c in itertools.combinations(algos, 2):
        stat, p = wilcoxon(means[a], means[c])
        pairs.append((a, c, stat, p))
    for (a, c, stat, p), p_holm in zip(pairs, holm([p for *_, p in pairs]), strict=True):
        verdict = "significant" if p_holm < 0.05 else "not significant"
        print(
            f"- Wilcoxon {a} vs {c}: W = {stat:.0f}, p = {p:.2g}, Holm p = {p_holm:.2g} "
            f"({verdict} at 5 %)"
        )

    print("\n## Winner (rule: feasible on every run, then mean gap, then mean time)\n")
    ranking = overall[feasible.reindex(overall.index).fillna(False)].sort_values(
        ["mean_gap", "mean_seconds"]
    )
    excluded = sorted(set(overall.index) - set(ranking.index))
    if excluded:
        print(f"Excluded (at least one infeasible run): {', '.join(excluded)}")
    print(ranking[["mean_gap", "mean_seconds"]].round(3).to_markdown())
    if len(ranking):
        print(f"\n**Winner: {ranking.index[0]}**")


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, in the input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


if __name__ == "__main__":
    main()
