"""Turn results/*.csv into the tables, figures and tests of the experimental study.

Usage:
    python experiments/analyze.py --results results
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402


def summary(df: pd.DataFrame) -> pd.DataFrame:
    """Mean, standard deviation and best cost, gap and time per (instance, algorithm)."""
    return (
        df.groupby(["instance", "n", "algorithm"])
        .agg(
            cost_mean=("cost", "mean"),
            cost_std=("cost", "std"),
            cost_best=("cost", "min"),
            gap_mean=("gap", "mean"),
            seconds_mean=("seconds", "mean"),
            feasible_rate=("feasible", "mean"),
        )
        .reset_index()
    )


def compare_algorithms(df: pd.DataFrame) -> pd.DataFrame:
    """Paired tests on the per-instance mean cost.

    Two algorithms: Wilcoxon signed-rank. Three or more: Friedman, then (TODO)
    a post-hoc Nemenyi test.
    """
    table = df.groupby(["instance", "algorithm"])["cost"].mean().unstack().dropna()
    algos = list(table.columns)
    rows = []
    if len(algos) >= 3:
        stat, p = stats.friedmanchisquare(*(table[a] for a in algos))
        rows.append({"test": "friedman", "algorithms": ",".join(algos), "stat": stat, "p": p})
    for i, a in enumerate(algos):
        for b in algos[i + 1 :]:
            if len(table) >= 5 and not np.allclose(table[a], table[b]):
                stat, p = stats.wilcoxon(table[a], table[b])
                rows.append({"test": "wilcoxon", "algorithms": f"{a},{b}", "stat": stat, "p": p})
    # TODO(Person 3): Holm correction for the pairwise p-values, Nemenyi post-hoc.
    return pd.DataFrame(rows)


def scaling_exponent(df: pd.DataFrame, algorithm: str) -> float:
    """Fit seconds ~ c * n^b on a log-log scale and return b (empirical complexity)."""
    sub = df[df["algorithm"] == algorithm].groupby("n")["seconds"].mean()
    if len(sub) < 2:
        return float("nan")
    slope, _ = np.polyfit(np.log(sub.index.values), np.log(sub.values), 1)
    return float(slope)


def plots(df: pd.DataFrame, out: Path) -> None:
    """Save the standard figures: cost spread per instance, time against n."""
    fig, ax = plt.subplots(figsize=(10, 4))
    df.boxplot(column="cost", by=["instance", "algorithm"], ax=ax, rot=90)
    ax.set_title("cost over seeds")
    fig.suptitle("")
    fig.tight_layout()
    fig.savefig(out / "cost_boxplot.png", dpi=150)

    fig, ax = plt.subplots(figsize=(6, 4))
    for algo, sub in df.groupby("algorithm"):
        m = sub.groupby("n")["seconds"].mean()
        ax.loglog(m.index, m.values, "o-", label=algo)
    ax.set_xlabel("customers n")
    ax.set_ylabel("mean seconds")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "time_vs_n.png", dpi=150)
    # TODO(Person 3): gap by family (uniform, clustered, TW), convergence curves.


def main(argv: list[str] | None = None) -> int:
    """Load every CSV in the results folder and write the analysis next to it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    args = parser.parse_args(argv)

    files = sorted(args.results.glob("*.csv"))
    files = [f for f in files if not f.name.startswith("summary")]
    if not files:
        print("no results found; run `make benchmark` first")
        return 1
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

    summary(df).to_csv(args.results / "summary.csv", index=False)
    tests = compare_algorithms(df)
    tests.to_csv(args.results / "summary_tests.csv", index=False)
    plots(df, args.results)
    for algo in df["algorithm"].unique():
        print(f"{algo}: time grows like n^{scaling_exponent(df, algo):.2f}")
    print(tests.to_string(index=False) if len(tests) else "not enough instances for tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
