"""Simulated annealing on the shared Instance/Solution API, plus ALNS acceptance helpers."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

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


@dataclass
class SAParams:
    """SA settings, following the GRASPParams interface.

    Attributes:
        initial_temperature_factor: T0 = max(1, factor * construction distance).
        final_temperature: Temperature at the end of the cooling schedule.
        iterations: Maximum proposed move attempts, including early rejections.
            With no time limit, this also sets the length of the cooling schedule.
        time_limit: Search budget in seconds, including route construction.
            ``None`` disables the deadline and cools by proposed move count instead.
    """

    initial_temperature_factor: float = 0.005
    final_temperature: float = 0.02
    iterations: int = 10**9
    time_limit: float | None = 20.0

    def __post_init__(self):
        """Reject invalid budgets and temperatures before compiling or searching."""
        for name in ("initial_temperature_factor", "final_temperature"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if self.time_limit is not None and (
            not math.isfinite(self.time_limit) or self.time_limit <= 0
        ):
            raise ValueError("time_limit must be finite and positive or None")
        if not isinstance(self.iterations, (int, np.integer)) or self.iterations <= 0:
            raise ValueError("iterations must be a positive integer")


@dataclass
class SAResult:
    """SA output, with the same principal fields as GRASPResult.

    History stores best-improvement batch snapshots, not every proposed move.
    Runtime excludes synthetic compilation and includes final shared validation.
    """

    best: Solution | None
    cost: float
    runtime: float
    iterations: int
    history: list[dict] = field(default_factory=list)
    initial: Solution | None = None
    accepted: int = 0
    stop_reason: str = "time_limit"


def sa(
    inst: Instance,
    params: SAParams | None = None,
    seed: int | None = 0,
    verbose: bool = False,
    *,
    initial: Solution | None = None,
) -> SAResult:
    """Run SA through the same public call pattern as ``grasp(inst, params, seed)``.

    The instance's matrix defines both distance and static travel time. No
    rounding is applied here. ``best`` is independently checked with the shared
    ``Solution.violations`` evaluator; the input instance is never modified.
    """
    from cvrp.sa_static import anneal_static, warmup
    from cvrp.sa_vrptw import initialize, problem_from_instance, validate

    p = params or SAParams()
    if initial is not None:
        violations = initial.violations(inst)
        if violations:
            raise ValueError(f"Infeasible initial solution: {violations}")
    if inst.n_customers == 0:
        return SAResult(Solution([]), 0.0, 0.0, 0, stop_reason="empty_instance")
    problem = problem_from_instance(inst)
    warmup()
    engine_seed = int(np.random.SeedSequence().generate_state(1)[0]) if seed is None else seed
    started = time.perf_counter()
    try:
        out = anneal_static(
            problem,
            initialize,
            validate,
            seed=engine_seed,
            initial=None if initial is None else initial.copy().routes,
            time_limit=p.time_limit,
            max_iterations=p.iterations,
            initial_temperature_factor=p.initial_temperature_factor,
            final_temperature=p.final_temperature,
        )
    except TimeoutError:
        return SAResult(
            None, math.inf, time.perf_counter() - started, 0, stop_reason="initialization_timeout"
        )
    best = Solution([list(r) for r in out["routes"]])
    violations = best.violations(inst)
    if violations:
        raise RuntimeError(f"SA returned an infeasible solution: {violations}")
    cost = best.cost(inst)
    if not math.isclose(cost, out["metrics"]["distance"], rel_tol=0, abs_tol=1e-6):
        raise RuntimeError("SA distance disagrees with the shared evaluator")
    history = [
        dict(iteration=iteration, seconds=seconds, best=distance, routes=routes)
        for iteration, (seconds, distance, routes) in zip(
            out["history_iterations"], out["history"], strict=True
        )
    ]
    if verbose:
        for row in history:
            print(
                f"moves {row['iteration']:9d}  best {row['best']:9.1f}  "
                f"seconds {row['seconds']:.3f}"
            )
    return SAResult(
        best=best,
        cost=cost,
        runtime=time.perf_counter() - started,
        iterations=out["iterations"],
        history=history,
        initial=Solution(out["initial_routes"]),
        accepted=out["accepted"],
        stop_reason=out["stop_reason"],
    )


def simulated_annealing(
    inst: Instance,
    params: SAParams | None = None,
    seed: int | None = 0,
    verbose: bool = False,
    *,
    initial: Solution | None = None,
) -> SAResult:
    """Descriptive alias for :func:`sa`, returning the same SAResult interface."""
    return sa(inst, params, seed, verbose, initial=initial)
