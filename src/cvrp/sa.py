"""Simulated annealing: acceptance helpers (shared with ALNS) and a plain SA baseline."""

from __future__ import annotations

import math

import numpy as np

from cvrp.instance import Instance
from cvrp.solution import Solution


def initial_temperature(cost: float, worse_pct: float = 0.05, accept_prob: float = 0.5) -> float:
    """Return T0 so that a solution ``worse_pct`` worse is accepted with ``accept_prob``.

    Calibration used by Ropke and Pisinger (2006): solve
    exp(-worse_pct * cost / T0) = accept_prob for T0.
    """
    return -worse_pct * cost / math.log(accept_prob)


def accept(delta: float, temperature: float, rng: np.random.Generator) -> bool:
    """Metropolis criterion: always accept improvements, worse moves with exp(-delta / T)."""
    if delta <= 0:
        return True
    if temperature <= 0:
        return False
    return bool(rng.random() < math.exp(-delta / temperature))


def simulated_annealing(
    inst: Instance,
    initial: Solution,
    iterations: int = 100_000,
    cooling: float = 0.9995,
    seed: int | None = 0,
) -> Solution:
    """Plain SA baseline: one random small move per iteration, geometric cooling.

    Used in the experimental study as the reference the ALNS must beat.

    TODO(Person 2): implement. Draw a random relocate, swap or 2-opt move,
    compute its delta, call ``accept`` and cool with ``T *= cooling``. Keep the
    best solution seen and return it.
    """
    raise NotImplementedError("plain simulated annealing is not implemented yet")
