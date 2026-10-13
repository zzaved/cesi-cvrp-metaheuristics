"""Plots: routes on the plane and convergence curves."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from cvrp.instance import Instance
from cvrp.solution import Solution

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def plot_routes(inst: Instance, sol: Solution, ax: Axes | None = None, title: str = "") -> Axes:
    """Draw every route in its own color, the depot as a black square."""
    ax = ax or plt.subplots(figsize=(7, 7))[1]
    xy = inst.coords
    cmap = plt.get_cmap("tab20")
    for k, route in enumerate(sol.routes):
        path = np.array([0, *route, 0])
        ax.plot(xy[path, 0], xy[path, 1], "-o", ms=3, lw=1.2, color=cmap(k % 20))
    ax.plot(*xy[0], "ks", ms=9, label="depot")
    ax.set_title(title or f"{inst.name}: {len(sol)} routes, cost {sol.cost(inst):.1f}")
    ax.set_aspect("equal")
    ax.legend(loc="upper right")
    return ax


def plot_convergence(
    best: list[float], current: list[float] | None = None, ax: Axes | None = None
) -> Axes:
    """Plot best (and optionally current) cost against the iteration number."""
    ax = ax or plt.subplots(figsize=(8, 4))[1]
    if current is not None:
        ax.plot(current, lw=0.6, alpha=0.5, label="current")
    ax.plot(best, lw=1.5, label="best")
    ax.set_xlabel("iteration")
    ax.set_ylabel("cost")
    ax.legend()
    return ax
