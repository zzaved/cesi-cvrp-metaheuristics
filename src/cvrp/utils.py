"""Shared helpers: distance matrix, seeding and timing."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

import numpy as np


def distance_matrix(coords: np.ndarray, rounding: str | None = None) -> np.ndarray:
    """Return the full Euclidean distance matrix of a set of points.

    Vectorized with numpy broadcasting: O(n^2) memory, no Python loop. For
    several thousand nodes this is a few hundred MB in float64, which is fine on
    a laptop; switch to float32 if memory becomes a problem.

    Args:
        coords: Array of shape (n, 2) with x and y coordinates.
        rounding: ``None`` keeps exact distances, ``"nint"`` rounds to the
            nearest integer as in the CVRPLIB ``EUC_2D`` convention, ``"floor1"``
            truncates to one decimal as in the usual Solomon convention.

    Returns:
        Array of shape (n, n) with ``d[i, j]`` the distance between i and j.
    """
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff**2).sum(axis=-1))
    if rounding == "nint":
        dist = np.rint(dist)
    elif rounding == "floor1":
        dist = np.floor(dist * 10.0) / 10.0
    elif rounding is not None:
        raise ValueError(f"unknown rounding {rounding!r}")
    return dist


def make_rng(seed: int | None) -> np.random.Generator:
    """Return a numpy random generator; every stochastic function takes one."""
    return np.random.default_rng(seed)


@contextmanager
def timer() -> Iterator[dict[str, float]]:
    """Measure wall-clock time of a block.

    Example:
        >>> with timer() as t:
        ...     _ = sum(range(10))
        >>> t["seconds"] >= 0
        True
    """
    out: dict[str, float] = {"seconds": 0.0}
    start = time.perf_counter()
    try:
        yield out
    finally:
        out["seconds"] = time.perf_counter() - start


def gap_percent(cost: float, best_known: float) -> float:
    """Return the relative gap to the best known solution, in percent.

    gap(%) = 100 * (cost_ours - cost_best_known) / cost_best_known
    """
    return 100.0 * (cost - best_known) / best_known
