"""Plug the public SAParams/SAResult solver into the shared Solomon study."""

from __future__ import annotations

from cvrp.instance import Instance
from cvrp.sa import SAParams, SAResult, sa


def run_sa(
    inst: Instance,
    seed: int,
    time_limit: float | None,
    *,
    initial_temperature_factor: float = 0.005,
    final_temperature: float = 0.02,
    iterations: int = 10**9,
) -> SAResult:
    """Call SA through the same Instance/parameters/result pattern as GRASP."""
    return sa(
        inst,
        SAParams(
            time_limit=time_limit,
            initial_temperature_factor=initial_temperature_factor,
            final_temperature=final_temperature,
            iterations=iterations,
        ),
        seed=seed,
    )
