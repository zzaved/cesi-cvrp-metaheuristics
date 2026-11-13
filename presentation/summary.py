"""Every number of the deck, read from results/ into presentation/data/summary.json.

    python presentation/summary.py

The deck (build_deck.js) reads only this file, so a slide never carries a number typed by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent / "data" / "summary.json"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from cvrp.tabu import RHO  # noqa: E402

ORDER = ["grasp", "sa", "tabu"]


def r(x, k=2):
    """Round to k decimals, None for missing."""
    return None if pd.isna(x) else round(float(x), k)


def solomon() -> dict:
    """Round 1: Solomon gaps by class and overall."""
    b = pd.read_csv(RES / "solomon_benchmark.csv")
    b["class"] = b.instance.str.extract(r"^([A-Z]+\d)")[0]
    by_class = b.pivot_table(index="class", columns="algorithm", values="gap", aggfunc="mean")
    overall = b.groupby("algorithm").agg(
        mean=("gap", "mean"),
        worst=("gap", "max"),
        at_bks=("gap", lambda g: int((g <= 1e-6).sum())),
        within7=("gap", lambda g: 100 * (g <= 7).mean()),
        iterations=("iterations", "mean"),
    )
    return {
        "classes": list(by_class.index),
        "by_class": {a: [r(v) for v in by_class[a]] for a in ORDER},
        "overall": {a: {k: r(v) for k, v in overall.loc[a].items()} for a in ORDER},
        "runs": int(len(b) / 3),
    }


def homberger() -> dict:
    """Homberger scale study by algorithm, size and budget."""
    f = RES / "scale_homberger.csv"
    if not f.exists():
        return {}
    h = pd.read_csv(f)
    g = h.groupby(["algorithm", "n", "time_limit"]).agg(
        gap=("gap", "mean"),
        sd=("gap", "std"),
        feasible=("feasible", "mean"),
        iterations=("iterations", "mean"),
        routes=("routes", "mean"),
    )
    out = {
        "sizes": sorted(h.n.unique().tolist()),
        "budgets": sorted(h.time_limit.unique().tolist()),
        "rows": [],
    }
    for (a, n, t), row in g.iterrows():
        out["rows"].append(
            {
                "algorithm": a,
                "n": int(n),
                "time_limit": t,
                "gap": r(row.gap),
                "sd": r(row.sd),
                "feasible": r(row.feasible),
                "iterations": r(row.iterations, 0),
                "routes": r(row.routes, 1),
            }
        )
    return out


def synthetic() -> dict:
    """10 000 customer runs, against the best run and the radial bound."""
    f = RES / "scale_synthetic.csv"
    if not f.exists():
        return {}
    s = pd.read_csv(f)
    g = s.groupby("algorithm").agg(
        cost=("cost", "mean"),
        best=("cost", "min"),
        feasible=("feasible", "mean"),
        routes=("routes", "mean"),
        iterations=("iterations", "mean"),
        seconds=("seconds", "mean"),
        runs=("cost", "size"),
    )
    best = g.best.min()
    import scale_study

    inst = scale_study.synthetic()  # radial bound: every route costs at least 2 max d_0i
    radial = 2 * float((inst.dist[0, 1:] * inst.demands[1:]).sum()) / inst.capacity
    g["vs_bound"] = 100 * (g.cost / radial - 1)
    return {"lower_bound": r(radial, 0)} | {
        a: {k: r(v) for k, v in row.items()} | {"vs_best": r(100 * (row.cost / best - 1))}
        for a, row in g.iterrows()
    }


def sweep() -> list:
    """Uniform, no windows, 1 000 to 10 000 customers: gap to the radial bound, time per step."""
    import scale_study

    f = RES / "scale_sweep.csv"
    if not f.exists():
        return []
    d = pd.concat([pd.read_csv(f), pd.read_csv(RES / "scale_synthetic.csv")], ignore_index=True)
    bound = {}
    for n in d.n.unique():
        inst = scale_study.synthetic(int(n))
        bound[n] = 2 * float((inst.dist[0, 1:] * inst.demands[1:]).sum()) / inst.capacity
    d["vs_bound"] = 100 * (d.cost / d.n.map(bound) - 1)
    d["ms_per_iteration"] = 1000 * d.seconds / d.iterations.where(d.iterations > 0)
    cols = ["n", "algorithm", "time_limit", "feasible", "seconds", "iterations", "routes"]
    return [
        {
            **{k: row[k] for k in cols},
            "vs_bound": r(row.vs_bound),
            "ms_per_iteration": r(row.ms_per_iteration, 3),
        }
        for _, row in d.iterrows()
    ]


def cities() -> dict:
    """Real cities: costs, network metrics and the control runs."""
    c = pd.read_csv(RES / "city_benchmark.csv")
    if "multi_hour_routes" not in c:
        c["multi_hour_routes"] = float("nan")
    g = c.groupby(["city", "objective", "algorithm"]).agg(
        mean=("cost", "mean"),
        std=("cost", "std"),
        min=("cost", "min"),
        routes=("routes", "mean"),
        iterations=("iterations", "mean"),
        multi_hour=("multi_hour_routes", "mean"),
    )
    m = pd.read_csv(RES / "city_metrics.csv").set_index("city")
    ctl = pd.read_csv(RES / "city_control.csv")
    ctl = ctl.groupby(["city", "algorithm", "time_limit", "kicks"], dropna=False).cost.agg(
        ["mean", "min"]
    )
    return {
        "costs": [
            {
                "city": k[0],
                "objective": k[1],
                "algorithm": k[2],
                "mean": r(v["mean"]),
                "best": r(v["min"]),
                "std": r(v["std"]),
                "routes": r(v["routes"], 1),
                "iterations": r(v["iterations"], 0),
                "multi_hour": r(v["multi_hour"], 1),
            }
            for k, v in g.iterrows()
        ],
        "metrics": {city: {k: r(v) for k, v in row.items()} for city, row in m.iterrows()},
        "control": [
            {
                "city": k[0],
                "algorithm": k[1],
                "time_limit": k[2],
                "kicks": None if pd.isna(k[3]) else int(k[3]),
                "mean": r(v["mean"]),
                "best": r(v["min"]),
            }
            for k, v in ctl.iterrows()
        ],
    }


def pilot() -> list[dict]:
    """300 customers per city, full model (traffic and windows): Tabu Search against GRASP-ILS."""
    c = pd.read_csv(RES / "city_pilot.csv")
    g = c.groupby(["city", "algorithm"]).agg(
        mean=("cost", "mean"), best=("cost", "min"), iterations=("iterations", "mean")
    )
    return [
        {
            "city": k[0],
            "algorithm": k[1],
            "mean": r(v["mean"]),
            "best": r(v["best"]),
            "iterations": r(v["iterations"], 0),
        }
        for k, v in g.iterrows()
    ]


def sensitivity() -> dict:
    """One factor at a time curves of each algorithm that has been run."""
    import sensitivity as sens

    out = {}
    for algo in ORDER:
        if (RES / f"sensitivity_{algo}.csv").exists():
            cur = sens.curves(algo)
            out[algo] = [
                {k: (r(v) if isinstance(v, float) and k != "value" else v) for k, v in row.items()}
                for row in cur.to_dict("records")
            ]
    return out


def exact() -> dict:
    """Largest sizes proven optimal by the ILP."""
    tw = pd.read_csv(RES / "exact_cvrptw.csv")
    td = pd.read_csv(RES / "exact_traffic.csv")
    base = td.instance.str.split("[").str[0]
    proven = td[td.status.eq("Optimal")].groupby(base).n.max()
    full = tw[(tw.n == 100) & tw.status.eq("Optimal")].instance.str.split("[").str[0]
    return {
        "traffic_min_n": int(proven.min()),
        "traffic_max_n": int(proven.max()),
        "tw_proven_100": sorted(full.tolist()),
    }


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    data = {
        "rho": list(RHO),
        "solomon": solomon(),
        "homberger": homberger(),
        "synthetic": synthetic(),
        "sweep": sweep(),
        "cities": cities(),
        "pilot": pilot(),
        "sensitivity": sensitivity(),
        "exact": exact(),
    }
    OUT.write_text(json.dumps(data, indent=1, default=str))
    print(json.dumps(data, default=str)[:3000])
