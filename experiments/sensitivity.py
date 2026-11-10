"""Sensitivity of each metaheuristic to its own parameters, one factor at a time.

Protocol: start from the tuned setting of each algorithm (section 8.1 of the final notebook),
change one parameter at a time over a range, keep the others fixed. Same 6 tuning instances,
same 20 s budget and same evaluator as experiments/solomon_study.py; 3 seeds per point. The test
instances are not used, so the comparison of section 8 stays clean.

Usage (each author runs their own algorithm, on their own machine):
    python experiments/sensitivity.py tabu    # -> results/sensitivity_tabu.csv
    python experiments/sensitivity.py sa      # -> results/sensitivity_sa.csv
    python experiments/sensitivity.py grasp   # -> results/sensitivity_grasp.csv
    python experiments/sensitivity.py plot tabu   # -> results/sensitivity_tabu.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import solomon_study as study  # noqa: E402

SEEDS = [101, 102, 103]

# algorithm -> (tuned setting, {parameter: values to try})
SENSITIVITY = {
    "tabu": (
        {"tenure": 20, "candidates": 200, "k_near": 15},
        {
            "tenure": [2, 5, 10, 20, 35, 50, 80],
            "candidates": [25, 50, 100, 200, 400, 800],
            "k_near": [5, 10, 15, 25, 40, 60],
        },
    ),
    "sa": (
        {"initial_temperature_factor": 0.005, "final_temperature": 0.005},
        {
            "initial_temperature_factor": [0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.05],
            "final_temperature": [0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.1],
        },
    ),
    "grasp": (
        {"alpha": 0.3, "improvement": "first", "perturb_kicks": 90},
        {
            "alpha": [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0],
            "perturb_kicks": [0, 15, 30, 60, 90, 150, 250],
            "n_neighbors": [5, 10, 20, 40],
        },
    ),
}


def jobs(algo: str) -> list[tuple[str, str, dict, int]]:
    """Every (tuning instance, algorithm, setting, seed), each distinct setting once."""
    base, ranges = SENSITIVITY[algo]
    settings = [dict(base)]
    for name, values in ranges.items():
        for v in values:
            s = {**base, name: v}
            if s not in settings:
                settings.append(s)
    return [(n, algo, s, seed) for s in settings for n in study.TUNING for seed in SEEDS]


def curves(algo: str) -> pd.DataFrame:
    """One row per (parameter, value): mean gap, spread over seeds, iterations."""
    base, ranges = SENSITIVITY[algo]
    df = pd.read_csv(study.RESULTS / f"sensitivity_{algo}.csv")
    df["setting"] = df.params.map(eval)  # written by this script from dicts of numbers and words
    rows = []
    for name, values in ranges.items():
        for v in values:
            want = {**base, name: v}
            runs = df[df.setting.map(lambda s, w=want: s == w)]
            per_seed = runs.groupby("seed").gap.mean()  # mean over the 6 instances, per seed
            rows.append(
                {
                    "parameter": name,
                    "value": v,
                    "tuned": v == base.get(name),
                    "mean_gap": runs.gap.mean(),
                    "seed_std": per_seed.std(),
                    "worst_gap": runs.gap.max(),
                    "iterations": runs.iterations.mean(),
                    "runs": len(runs),
                }
            )
    return pd.DataFrame(rows)


def plot(algo: str) -> None:
    """One panel per parameter: mean gap against the value, band = one std over seeds."""
    import matplotlib.pyplot as plt

    c = curves(algo)
    names = list(SENSITIVITY[algo][1])
    fig, axes = plt.subplots(1, len(names), figsize=(4.2 * len(names), 3.4), sharey=True)
    for ax, name in zip(axes, names, strict=True):
        p = c[c.parameter == name]
        x = list(range(len(p))) if p.value.dtype == object else p.value
        ax.plot(x, p.mean_gap, marker="o", lw=2, color="#2a6fdb")
        ax.fill_between(
            x, p.mean_gap - p.seed_std, p.mean_gap + p.seed_std, alpha=0.2, color="#2a6fdb"
        )
        tuned = p[p.tuned]
        ax.scatter(
            x[tuned.index[0] - p.index[0]] if p.value.dtype == object else tuned.value,
            tuned.mean_gap,
            s=90,
            facecolor="none",
            edgecolor="black",
            zorder=3,
            label="tuned",
        )
        if p.value.dtype == object:
            ax.set_xticks(x, p.value)
        elif p.value.min() > 0 and p.value.max() / p.value.min() >= 20:
            ax.set_xscale("log")
            ax.set_xticks(p.value, [f"{v:g}" for v in p.value])
            ax.minorticks_off()
        ax.set_xlabel(name)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("mean gap on the tuning set (%)")
    axes[0].legend()
    fig.suptitle(f"Sensitivity of {algo}: one parameter at a time, 6 instances, 3 seeds, 20 s")
    fig.tight_layout()
    fig.savefig(study.RESULTS / f"sensitivity_{algo}.png", dpi=150)
    print(c.round(3).to_string(index=False))


if __name__ == "__main__":
    if sys.argv[1] == "plot":
        plot(sys.argv[2])
    else:
        algo = sys.argv[1]
        study.run(jobs(algo), study.RESULTS / f"sensitivity_{algo}.csv")
