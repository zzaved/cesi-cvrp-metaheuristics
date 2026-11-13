"""Animated figures of the final presentation (GIF), from real runs of the three solvers.

    python presentation/figures.py runs     # solver runs -> presentation/data/*.json (about 3 min)
    python presentation/figures.py render   # GIFs and PNGs -> presentation/img/
    python presentation/figures.py render paris   # one figure only

Every frame shows a solution returned by a solver and checked by the shared evaluator; nothing is
drawn by hand. Run `runs` alone on the machine (the runs are time limited).
"""

from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

HERE = Path(__file__).resolve().parent
DATA, IMG = HERE / "data", HERE / "img"
CREAM, NAVY, COBALT, VERM, SOFT, OCHRE = (
    "#f4f0e5",
    "#1b2b6b",
    "#2547c9",
    "#c0391b",
    "#5a679e",
    "#c98b1e",
)
ALGO = {
    "tabu": ("Tabu Search", OCHRE),
    "sa": ("Simulated Annealing", VERM),
    "grasp": ("GRASP-ILS", COBALT),
}
SNAPSHOTS = [0.3, 0.6, 1.0, 2.0, 4.0, 8.0, 14.0, 20.0]
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "text.color": NAVY,
        "axes.labelcolor": NAVY,
        "xtick.color": SOFT,
        "ytick.color": SOFT,
        "axes.edgecolor": SOFT,
    }
)


# ----------------------------------------------------------------------------------- runs
def _routes_cost(algo: str, inst, seed: int, limit: float):
    from scale_study import solve

    from cvrp.solution import Solution

    routes, _ = solve(algo, inst, seed, limit)
    sol = Solution(routes=[list(map(int, r)) for r in routes if len(r)])
    assert sol.is_feasible(inst)
    return sol.routes, sol.cost(inst)


def race_job(job):
    """Best solution of one algorithm on RC101 after `limit` seconds (seed 1)."""
    import solomon_study

    algo, limit = job
    inst = solomon_study.load("RC101")
    routes, cost = _routes_cost(algo, inst, 1, limit)
    return {"algo": algo, "limit": limit, "routes": routes, "cost": cost}


def convergence_job(algo):
    """Best cost against time on Homberger R1_10_1 (1 000 customers), one 60 s run."""
    import homberger_study
    from sa_adapter import run_sa

    from cvrp.grasp import GRASPParams, grasp
    from cvrp.tabu import TabuParams, distance_cost, tabu_search

    inst = homberger_study.load("R1_10_1")
    if algo == "tabu":
        r = tabu_search(
            inst, distance_cost(inst), TabuParams(tenure=20, candidates=200, time_limit=60.0), 1
        )
        hist = [(float(s), float(c)) for s, c in r.history]
    elif algo == "grasp":
        r = grasp(
            inst,
            GRASPParams(
                alpha=0.3, improvement="first", perturb_kicks=90, iterations=10**9, time_limit=60.0
            ),
            seed=1,
        )
        hist = [(h["seconds"], h["best"]) for h in r.history]
    else:
        r = run_sa(inst, 1, 60.0, initial_temperature_factor=0.01, final_temperature=0.005)
        hist = [(h["seconds"], h["best"]) for h in r.history]
    return {"algo": algo, "history": hist, "best_known": inst.best_known}


def city_job(start):
    """Tabu Search on Paris (999 customers), duration with traffic, leaving at `start` minutes."""
    from city_study import instance, solve

    objective = "duration 08:00" if start == 480.0 else "duration 22:00"
    inst = instance("Paris", objective)
    routes, cost, _ = solve("tabu", inst, start, 1, 30.0)
    return {
        "start": start,
        "routes": [list(map(int, r)) for r in routes if len(r)],
        "cost": float(cost),
    }


def runs() -> None:
    """Run the three solver studies used by the animations."""
    DATA.mkdir(exist_ok=True)
    with Pool(3) as pool:
        race = pool.map(race_job, [(a, t) for a in ALGO for t in SNAPSHOTS])
        (DATA / "race_rc101.json").write_text(json.dumps(race))
        conv = pool.map(convergence_job, list(ALGO))
        (DATA / "convergence_r1_10_1.json").write_text(json.dumps(conv))
        city = pool.map(city_job, [480.0, 1320.0])
        (DATA / "paris_day_night.json").write_text(json.dumps(city))


# --------------------------------------------------------------------------------- render
def _ax_clean(ax):
    ax.set_facecolor(CREAM)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _palette(k: int):
    cols = [COBALT, VERM, OCHRE, NAVY, "#3f8f6b", "#8a4fa3", "#d0632f", "#2f8fb0", SOFT]
    return cols[k % len(cols)]


def render_race() -> None:
    """Three panels, the same instance, the best solution of each algorithm as time passes."""
    import solomon_study

    inst = solomon_study.load("RC101")
    xy, bk = inst.coords, inst.best_known
    race = json.loads((DATA / "race_rc101.json").read_text())
    snap = {(r["algo"], r["limit"]): r for r in race}
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.2), facecolor=CREAM)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.83, bottom=0.02, wspace=0.04)
    frames = [t for t in SNAPSHOTS for _ in range(4)] + [SNAPSHOTS[-1]] * 12

    def draw(i):
        t = frames[i]
        for ax, algo in zip(axes, ALGO, strict=True):
            ax.clear()
            _ax_clean(ax)
            name, col = ALGO[algo]
            r = snap[(algo, t)]
            for k, route in enumerate(r["routes"]):
                p = [0, *route, 0]
                ax.plot(*xy[p].T, "-", lw=1.4, color=_palette(k), alpha=0.9)
            ax.scatter(*xy[1:].T, s=9, color=NAVY, zorder=3)
            ax.scatter(*xy[0], s=110, marker="s", color=VERM, zorder=4)
            gap = 100 * (r["cost"] / bk - 1)
            ax.set_title(
                f"{name}\ncost {r['cost']:.0f}   gap {gap:.1f} %   {len(r['routes'])} trucks",
                color=col,
                fontsize=13,
                fontweight="bold",
            )
        fig.suptitle(
            f"Solomon RC101, 100 customers with time windows   t = {t:g} s",
            color=NAVY,
            fontsize=15,
        )

    FuncAnimation(fig, draw, frames=len(frames)).save(
        IMG / "race_rc101.gif", writer=PillowWriter(fps=4), dpi=90
    )
    plt.close(fig)


def render_convergence() -> None:
    """Best gap against time, drawn as the clock runs, on 1 000 customers."""
    conv = json.loads((DATA / "convergence_r1_10_1.json").read_text())
    fig, ax = plt.subplots(figsize=(11, 5.2), facecolor=CREAM)
    ax.set_facecolor(CREAM)
    clocks = np.linspace(0.5, 60, 60)
    frames = list(clocks) + [60.0] * 12

    def draw(i):
        t = frames[i]
        ax.clear()
        ax.set_facecolor(CREAM)
        for run in conv:
            name, col = ALGO[run["algo"]]
            h = np.array(run["history"])
            g = 100 * (h[:, 1] / run["best_known"] - 1)
            keep = h[:, 0] <= t
            if keep.any():
                xs = np.append(h[keep, 0], t)
                ys = np.append(g[keep], g[keep][-1])
                ax.step(xs, ys, where="post", color=col, lw=2.6, label=f"{name}: {ys[-1]:.1f} %")
                ax.plot(t, ys[-1], "o", color=col, ms=8)
        ax.set(xlim=(0, 61), ylim=(0, 45), xlabel="seconds", ylabel="gap to best known (%)")
        ax.axhline(7, color=SOFT, ls=":", lw=1)
        ax.text(0.5, 7.6, "7 % target", color=SOFT, ha="left")
        ax.legend(loc="upper right", frameon=False, fontsize=12)
        ax.set_title(
            f"Homberger R1_10_1, 1 000 customers with time windows   t = {t:.0f} s", fontsize=14
        )
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    FuncAnimation(fig, draw, frames=len(frames)).save(
        IMG / "convergence_r1_10_1.gif", writer=PillowWriter(fps=8), dpi=90
    )
    plt.close(fig)


def _schedule(route, dist, start, rho):
    """(time, node) along a route leaving the depot at `start`, trip i->j takes rho[hour] d_ij."""
    t, i, out = start, 0, [(start, 0)]
    for j in [*route, 0]:
        t += rho[int(t // 60) % 24] * dist[i, j]
        out.append((t, j))
        i = j
    return out


def render_paris() -> None:
    """Trucks of the same Paris plan type leaving at 08:00 and at 22:00, one clock."""
    from city_study import instance

    from cvrp.tabu import RHO

    inst = instance("Paris", "duration 08:00")
    pts = np.load(ROOT / "data" / "cities" / "Paris_data.npz")["points"]
    xy = np.c_[pts[:, 1], pts[:, 0]]  # lon, lat
    city = {c["start"]: c for c in json.loads((DATA / "paris_day_night.json").read_text())}
    plans = {s: [_schedule(r, inst.dist, s, RHO) for r in city[s]["routes"]] for s in city}
    span = max(sch[-1][0] - s for s, p in plans.items() for sch in p)
    clocks = np.linspace(0, span, 60)
    frames = list(clocks) + [span] * 10
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.2), facecolor=CREAM)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.03)

    def where(sch, t):
        times = [a for a, _ in sch]
        if t >= times[-1]:
            return xy[0], len(sch) - 1, True
        k = int(np.searchsorted(times, t, side="right")) - 1
        (t0, a), (t1, b) = sch[k], sch[k + 1]
        f = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
        return xy[a] + f * (xy[b] - xy[a]), k, False

    def draw(i):
        dt = frames[i]
        for ax, start in zip(axes, (480.0, 1320.0), strict=True):
            ax.clear()
            _ax_clean(ax)
            ax.scatter(*xy[1:].T, s=3, color=SOFT, alpha=0.5)
            done = 0
            for k, sch in enumerate(plans[start]):
                pos, idx, back = where(sch, start + dt)
                path = np.array([xy[n] for _, n in sch[: idx + 1]] + [pos])
                if back:  # finished routes fade, trucks on the road stand out
                    ax.plot(*path.T, lw=0.6, color=SOFT, alpha=0.35)
                else:
                    ax.plot(*path.T, lw=1.4, color=_palette(k), alpha=0.95)
                    ax.plot(*pos, "o", ms=6, color=_palette(k), mec="white", mew=0.8)
                done += back
            ax.scatter(*xy[0], s=120, marker="s", color=VERM, zorder=5)
            clock = (start + dt) % 1440
            label = "leave 08:00 (peak traffic)" if start == 480 else "leave 22:00 (night)"
            ax.set_title(
                f"{label}\nclock {int(clock // 60):02d}:{int(clock % 60):02d}   "
                f"trucks back {done}/{len(plans[start])}   total "
                f"{city[start]['cost']:.0f} min",
                fontsize=13,
                color=NAVY,
            )
        fig.suptitle(
            "Paris, 999 real customers, travel times from the road network (Tabu Search, 30 s)",
            fontsize=14,
            color=NAVY,
        )

    FuncAnimation(fig, draw, frames=len(frames)).save(
        IMG / "paris_day_night.gif", writer=PillowWriter(fps=7), dpi=72
    )
    plt.close(fig)


EQUATIONS = {
    "eq_v1": r"$\min\ z = \sum_{(i,j) \in A}\ c_{ij}\, x_{ij}$",
    "eq_v2": r"$\min\ z = \sum_{k \in K}\ (t^{k}_{n+1} - t^{k}_{0})$",
    "eq_traffic": r"$c^{h}_{ij} = \rho_h\, c_{ij}$",
    "eq_arrival": r"$a_j = t_i + s_i + \sum_h c^{h}_{ij}\, y_{ih}\quad$ if truck goes $i \to j$",
    "eq_gap": r"$\mathrm{gap} = 100\ \frac{\mathrm{cost} - \mathrm{BKS}}{\mathrm{BKS}}$",
    "eq_lb": r"$LB = \frac{2}{Q} \sum_{i=1}^{n} d_{0i}\, q_i$",
}


def render_equations(color: str = NAVY) -> None:
    """Formulas as transparent PNG (mathtext), so the slides show mathematics, not code.

    Each formula is written twice: navy for light slides, white (``*_white.png``) for dark boxes.
    """
    for name, tex in EQUATIONS.items():
        for suffix, col in (("", color), ("_white", "#FFFFFF")):
            fig = plt.figure(figsize=(0.01, 0.01))
            fig.text(0, 0, tex, fontsize=30, color=col, math_fontfamily="cm")
            fig.savefig(
                IMG / f"{name}{suffix}.png",
                dpi=220,
                transparent=True,
                bbox_inches="tight",
                pad_inches=0.05,
            )
            plt.close(fig)


def render(only: str | None = None) -> None:
    """Write every GIF and formula image (or only one of them: race, convergence, paris)."""
    IMG.mkdir(exist_ok=True)
    steps = {
        "equations": render_equations,
        "race": render_race,
        "convergence": render_convergence,
        "paris": render_paris,
    }
    for name, step in steps.items():
        if only in (None, name):
            step()


if __name__ == "__main__":
    if sys.argv[1] == "runs":
        runs()
    else:  # render [equations|race|convergence|paris]
        render(sys.argv[2] if len(sys.argv) > 2 else None)
