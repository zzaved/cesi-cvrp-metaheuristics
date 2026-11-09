"""SA problem model, independent evaluator and experiment helpers."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import vrplib

from cvrp.sa_static import anneal_static, warmup

SEEDS = tuple(range(10))


@dataclass
class Problem:
    """Routing arrays, objective mode and arc convention for SA."""

    name: str
    xy: np.ndarray
    q: np.ndarray
    tw: np.ndarray
    service: np.ndarray
    capacity: float
    max_vehicles: int
    distance: np.ndarray
    mode: str = "distance"
    departure_step: float = 15.0
    distance_convention: str = "truncated"

    @property
    def n(self):
        """Number of non-depot customers."""
        return len(self.q) - 1


def make_problem(raw, n=None, mode="distance", distance_convention=None):
    """Build routing arrays, using truncated arcs by default."""
    if mode not in {"benchmark", "distance", "traffic"}:
        raise ValueError("Unknown optimization mode")
    distance_convention = distance_convention or ("exact" if mode == "traffic" else "truncated")
    if distance_convention not in {"truncated", "exact"}:
        raise ValueError("Unknown distance convention")
    n = len(raw["demand"]) - 1 if n is None else n
    xy = np.array(raw["node_coord"][: n + 1], dtype=float)
    d = np.linalg.norm(xy[:, None] - xy[None, :], axis=2)
    # Convention DIMACS/PyVRP: truncate each arc to one decimal.
    if distance_convention == "truncated":
        d = np.floor(d * 10 + 1e-9) / 10
    service = np.asarray(raw["service_time"], dtype=float)
    if service.ndim == 0:
        service = np.full(n + 1, float(service))
    else:
        service = service[: n + 1].copy()
    service[0] = 0
    return Problem(
        raw.get("name", "instance") + f"-{n}",
        xy,
        np.array(raw["demand"][: n + 1], dtype=float),
        np.array(raw["time_window"][: n + 1], dtype=float),
        service,
        float(raw["capacity"]),
        int(raw.get("vehicles", n)),
        d,
        mode,
        distance_convention=distance_convention,
    )


RHO = np.array(
    [
        1,
        1,
        1,
        1,
        1,
        1.05,
        1.30,
        1.75,
        1.80,
        1.40,
        1.20,
        1.25,
        1.30,
        1.25,
        1.20,
        1.25,
        1.45,
        1.80,
        1.75,
        1.40,
        1.10,
        1.05,
        1,
        1,
    ]
)


def simulate(p, route, departure=0.0):
    """Independent forward schedule; None if infeasible. Times use instance units."""
    if not route:
        return dict(
            distance=0.0, duration=0.0, departure=departure, return_time=departure, rows=[]
        )
    if sum(p.q[i] for i in route) > p.capacity + 1e-8:
        return None
    if departure < p.tw[0, 0] - 1e-8 or departure > p.tw[0, 1] + 1e-8:
        return None
    t, prev, distance, rows = departure, 0, 0.0, []
    for j in list(route) + [0]:
        length = p.distance[prev, j]
        multiplier = RHO[int(t // 60) % 24] if p.mode == "traffic" else 1.0
        arrive = t + length * multiplier
        start = max(arrive, p.tw[j, 0])
        if start > p.tw[j, 1] + 1e-8:
            return None
        rows.append(
            dict(customer=j, leave_previous=t, arrival=arrive, start=start, waiting=start - arrive)
        )
        t = start + p.service[j]
        distance += length
        prev = j
    return dict(
        distance=distance, duration=t - departure, departure=departure, return_time=t, rows=rows
    )


def evaluate_route(p, route):
    """Return route objective and an independent feasible schedule."""
    if not route:
        return 0.0, None
    if p.mode != "traffic":
        sch = simulate(p, route, p.tw[0, 0])
    else:
        # Approximation explicit: grid of depot departures, earliest service thereafter.
        sch = None
        for dep in np.arange(p.tw[0, 0], p.tw[0, 1] + 1e-8, p.departure_step):
            candidate = simulate(p, route, float(dep))
            if candidate is not None and (sch is None or candidate["duration"] < sch["duration"]):
                sch = candidate
    if sch is None:
        return math.inf, None
    return sch["distance" if p.mode != "traffic" else "duration"], sch


def validate(p, routes):
    """Recompute from scratch: coverage, capacity, windows, fleet, returned objective."""
    flat = [i for r in routes for i in r]
    assert sorted(flat) == list(range(1, p.n + 1)), "Missing/duplicate/out-of-range customer"
    routes = [r for r in routes if r]
    assert len(routes) <= p.max_vehicles, "Fleet limit exceeded"
    schedules = []
    for r in routes:
        assert sum(p.q[i] for i in r) <= p.capacity + 1e-8
        cost, sch = evaluate_route(p, r)
        assert math.isfinite(cost), "Time window/depot violation"
        schedules.append(sch)
    return dict(
        vehicles=len(routes),
        distance=sum(s["distance"] for s in schedules),
        duration=sum(s["duration"] for s in schedules),
        schedules=schedules,
    )


def repair(p, routes, removed, rng, route_limit=8, deadline=math.inf):
    """Randomized cheapest feasible insertion; a new route is permitted."""
    routes = [list(r) for r in routes if r]
    rng.shuffle(removed)
    for customer in removed:
        if time.perf_counter() >= deadline:
            raise TimeoutError("SA time budget exhausted")
        options = []
        # Limit candidate routes by proximity for large instances.
        candidates = sorted(
            range(len(routes)), key=lambda k: min(p.distance[customer, j] for j in routes[k])
        )[:route_limit]
        for k in candidates:
            r = routes[k]
            if sum(p.q[i] for i in r) + p.q[customer] > p.capacity + 1e-8:
                continue
            old, _ = evaluate_route(p, r)
            for pos in range(len(r) + 1):
                if time.perf_counter() >= deadline:
                    raise TimeoutError("SA time budget exhausted")
                nr = r[:pos] + [customer] + r[pos:]
                cost, _ = evaluate_route(p, nr)
                if math.isfinite(cost):
                    options.append((cost - old, k, nr))
        if options:
            options.sort(key=lambda x: x[0])
            # Usually greedy, sometimes diversify between best insertions.
            choice = 0 if rng.random() < 0.9 else int(rng.integers(min(3, len(options))))
            _, k, nr = options[choice]
            routes[k] = nr
        elif len(routes) < p.max_vehicles and math.isfinite(evaluate_route(p, [customer])[0]):
            routes.append([customer])
        else:
            return None
    return routes


def initialize(p, rng, deadline=math.inf):
    """Construct feasible routes without reference information."""
    # Independent of all reference routes and values.
    for _ in range(50):
        out = repair(p, [], list(range(1, p.n + 1)), rng, deadline=deadline)
        if out is not None:
            return out
    raise RuntimeError("No feasible initialization; increase construction effort or check data.")


def anneal(
    p, seed=0, alpha=0.995, min_temperature=0.001, initial=None, time_limit=20.0, accelerated=False
):
    """Dispatch compiled static SA or the Python fallback."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between 0 and 1")
    if min_temperature <= 0:
        raise ValueError("min_temperature must be positive")
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    if accelerated and p.mode != "traffic":
        return anneal_static(
            p, initialize, validate, seed=seed, initial=initial, time_limit=time_limit
        )
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    deadline = started + time_limit
    current = initialize(p, rng, deadline) if initial is None else [list(r) for r in initial]
    validate(p, current)
    # Safe distance upper bound for n customers and <=n nonempty routes.
    # Thus one fewer vehicle always dominates any distance change in benchmark mode.
    vehicle_weight = 2 * p.n * float(p.distance.max()) + 1
    cache = {}

    def route_cost(r):
        key = tuple(r)
        if key not in cache:
            cache[key] = evaluate_route(p, r)[0]
        return cache[key]

    def energy(rs):
        return sum(route_cost(r) for r in rs) + (
            vehicle_weight * len(rs) if p.mode == "benchmark" else 0
        )

    current_e = energy(current)
    best, best_e = [r[:] for r in current], current_e
    initial_metrics = validate(p, current)
    # Temperature controls distance worsening; vehicle reduction remains strongly preferred.
    initial_temperature = max(1.0, 0.05 * sum(route_cost(r) for r in current))
    temperature = initial_temperature
    history = [(0.0, sum(route_cost(r) for r in best), len(best))]
    iteration = accepted = 0
    while temperature > min_temperature and time.perf_counter() < deadline:
        iteration += 1
        candidate = [r[:] for r in current]
        if rng.random() < 0.65:
            # Ruin/repair changes assignment and can eliminate a complete route.
            k = int(rng.integers(len(candidate)))
            if rng.random() < 0.35:
                removed = candidate.pop(k)
            else:
                pool = [i for r in candidate for i in r]
                count = min(len(pool), int(rng.integers(2, min(12, p.n) + 1)))
                removed = rng.choice(pool, count, replace=False).tolist()
                delete = set(removed)
                candidate = [[i for i in r if i not in delete] for r in candidate]
            try:
                candidate = repair(p, candidate, removed, rng, deadline=deadline)
            except TimeoutError:
                break
        else:
            a, b = rng.integers(len(candidate), size=2)
            if a == b:
                if len(candidate[a]) < 2:
                    continue
                u, v = sorted(rng.choice(len(candidate[a]), 2, replace=False))
                candidate[a][u : v + 1] = reversed(candidate[a][u : v + 1])
            else:
                u, v = int(rng.integers(len(candidate[a]))), int(rng.integers(len(candidate[b])))
                candidate[a][u], candidate[b][v] = candidate[b][v], candidate[a][u]
        if candidate is None:
            continue
        candidate = [r for r in candidate if r]
        new_e = energy(candidate)
        delta = new_e - current_e
        if math.isfinite(new_e) and (delta <= 0 or rng.random() < math.exp(-delta / temperature)):
            current, current_e = candidate, new_e
            accepted += 1
            if new_e < best_e - 1e-8:
                best, best_e = [r[:] for r in current], new_e
                history.append(
                    (time.perf_counter() - started, sum(route_cost(r) for r in best), len(best))
                )
        if len(cache) > 100000:
            cache.clear()
        temperature *= alpha
    search_elapsed = time.perf_counter() - started
    metrics = validate(p, best)
    return dict(
        routes=best,
        metrics=metrics,
        initial=initial_metrics,
        seed=seed,
        elapsed=time.perf_counter() - started,
        search_elapsed=search_elapsed,
        time_limit=time_limit,
        stop_reason=("time_limit" if time.perf_counter() >= deadline else "temperature"),
        iterations=iteration,
        accepted=accepted,
        history=history,
    )


def print_gap_conclusions(name, table):
    """Print seed variability and the shortest-distance run."""
    best = table.loc[table.distance.idxmin()]
    print(
        f"\nConclusion - {name}: mean gap {table.gap_pct.mean():.2f}%; "
        f"range {table.gap_pct.min():.2f}% to {table.gap_pct.max():.2f}%."
    )
    print(
        f"Best distance: seed {int(best.seed)}, {best.gap_pct:.2f}%, "
        f"{int(best.vehicles)} trucks vs {int(best.reference_vehicles)} in the reference."
    )
    if len(table) == 1:
        print("Only one seed: variability is not yet measured.")


def load_solomon(data, name, n=None):
    """Read a local Solomon-format .txt and its truncated-distance reference."""
    data = Path(data)
    raw = vrplib.read_instance(data / f"{name}.txt", instance_format="solomon")
    reference = vrplib.read_solution(data / f"{name}.sol")
    problem = make_problem(raw, n=n, mode="distance", distance_convention="truncated")
    routes = [[int(i) for i in r if n is None or i <= problem.n] for r in reference["routes"]]
    routes = [r for r in routes if r]
    metrics = validate(problem, routes)
    if n is None and not np.isclose(metrics["distance"], reference["cost"], rtol=0, atol=1e-6):
        raise ValueError(f"{name}: reference cost does not match truncated arcs")
    return problem, routes


def problem_from_instance(inst):
    """Read the shared Instance without recomputing or modifying its distance matrix."""
    size = inst.n_customers + 1
    windows = (
        np.column_stack((inst.ready_times, inst.due_times))
        if inst.has_time_windows
        else np.column_stack((np.zeros(size), np.full(size, np.inf)))
    )
    service = (
        np.asarray(inst.service_times, dtype=float).copy()
        if inst.service_times is not None
        else np.zeros(size)
    )
    if service[0] != 0:
        raise ValueError("SA expects zero depot service time")
    return Problem(
        name=inst.name,
        xy=np.asarray(inst.coords, dtype=float),
        q=np.asarray(inst.demands, dtype=float),
        tw=np.ascontiguousarray(windows, dtype=float),
        service=service,
        capacity=float(inst.capacity),
        max_vehicles=inst.num_vehicles if inst.num_vehicles is not None else inst.n_customers,
        distance=np.ascontiguousarray(inst.dist, dtype=float),
        mode="distance",
        distance_convention="instance_matrix",
    )


def _run_tabu(p, seed, time_limit):
    from cvrp.instance import Instance
    from cvrp.tabu import TabuParams, distance_cost, tabu_search

    inst = Instance(
        name=p.name,
        coords=p.xy,
        demands=p.q,
        capacity=p.capacity,
        num_vehicles=p.max_vehicles,
        ready_times=p.tw[:, 0],
        due_times=p.tw[:, 1],
        service_times=p.service,
        dist=p.distance,
    )
    started = time.perf_counter()
    result = tabu_search(inst, distance_cost(inst), TabuParams(time_limit=time_limit), seed)
    metrics = validate(p, result.routes)
    return dict(
        metrics=metrics,
        routes=result.routes,
        elapsed=time.perf_counter() - started,
        iterations=result.iterations,
        stop_reason="time_limit",
        initial=None,
    )


def _run_seed(job):
    p, ref_routes, seed, algorithm, time_limit, alpha, min_temperature = job
    ref = validate(p, ref_routes)
    if algorithm == "sa":
        out = anneal(
            p,
            seed=seed,
            alpha=alpha,
            min_temperature=min_temperature,
            time_limit=time_limit,
            accelerated=True,
        )
        unit, engine = "proposed_move_attempts", "numba"
        candidates = out["iterations"]
    elif algorithm == "tabu":
        if p.mode != "distance":
            raise ValueError("Tabu comparison requires the distance-only objective")
        out = _run_tabu(p, seed, time_limit)
        unit, engine = "outer_iterations", "python"
        candidates = out["iterations"] * 200
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    m = out["metrics"]
    gap = 100 * (m["distance"] / ref["distance"] - 1)
    initial = out["initial"] or {}
    record = dict(
        instance=p.name,
        n=p.n,
        algorithm=algorithm,
        seed=seed,
        objective=p.mode,
        distance_convention=p.distance_convention,
        engine=engine,
        vehicles=m["vehicles"],
        distance=m["distance"],
        cost=m["distance"],
        gap_pct=gap,
        gap=gap,
        reference_distance=ref["distance"],
        reference_vehicles=ref["vehicles"],
        reference_feasible=True,
        feasible=True,
        elapsed_s=out["elapsed"],
        seconds=out["elapsed"],
        time_limit_s=time_limit,
        iterations=out["iterations"],
        iteration_unit=unit,
        candidate_attempts=candidates,
        iterations_per_s=out["iterations"] / out["elapsed"],
        stop_reason=out["stop_reason"],
        initial_distance=initial.get("distance"),
        initial_vehicles=initial.get("vehicles"),
    )
    return record, out


def _execute_jobs(jobs, workers):
    if workers < 1:
        raise ValueError("workers must be positive")
    if workers == 1:
        warmup()
        return [_run_seed(job) for job in jobs]
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=workers, initializer=warmup) as pool:
        return list(pool.map(_run_seed, jobs))


def run_experiment(
    p,
    ref_routes,
    seeds,
    alpha=0.995,
    min_temperature=0.001,
    time_limit=20.0,
    workers=1,
):
    """Run independent SA seeds; return raw rows and solutions without writing files."""
    jobs = [(p, ref_routes, seed, "sa", time_limit, alpha, min_temperature) for seed in seeds]
    results = _execute_jobs(jobs, workers)
    return pd.DataFrame([r for r, _ in results]), [o for _, o in results]


def solomon_names(data):
    """Discover every local .txt instance, requiring its paired .sol reference."""
    data = Path(data)
    paths = sorted(data.glob("*.txt"))
    if not paths:
        raise FileNotFoundError(f"No Solomon .txt instances found in {data}")
    for path in paths:
        if not path.with_suffix(".sol").is_file():
            raise FileNotFoundError(f"Missing reference: {path.with_suffix('.sol')}")
    return tuple(path.stem for path in paths)


def run_comparison(
    data, names=None, seeds=SEEDS, *, time_limit=20.0, workers=1, algorithms=("sa",)
):
    """Run SA on all supplied pairs by default; other solvers require explicit selection."""
    names = solomon_names(data) if names is None else names
    jobs = []
    for name in names:
        p, routes = load_solomon(data, name)
        for seed in seeds:
            for algorithm in algorithms:
                jobs.append((p, routes, seed, algorithm, time_limit, 0.995, 0.001))
    results = _execute_jobs(jobs, workers)
    return pd.DataFrame([r for r, _ in results])


def summarize_runs(records):
    """Per-instance, per-algorithm mean and sample standard deviation (ddof=1)."""
    return (
        records.groupby(["instance", "algorithm"], sort=True)
        .agg(
            runs=("seed", "size"),
            distance_mean=("distance", "mean"),
            distance_std=("distance", "std"),
            gap_mean=("gap_pct", "mean"),
            gap_std=("gap_pct", "std"),
            elapsed_mean=("elapsed_s", "mean"),
            elapsed_std=("elapsed_s", "std"),
            iterations_mean=("iterations", "mean"),
            iterations_std=("iterations", "std"),
        )
        .reset_index()
    )
