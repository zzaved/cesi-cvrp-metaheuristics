"""Compiled, feasible-move SA for static travel times.

Compilation is a setup step, separate from per-instance wall-clock budgets.
The independent notebook evaluator validates the final routes.
"""

from __future__ import annotations

import math
import time

import numpy as np
from numba import njit


@njit(cache=True)
def _cost(route, length, distance, demand, windows, service, capacity):
    clock = windows[0, 0]
    load = total = 0.0
    previous = 0
    for pos in range(length + 1):
        node = route[pos] if pos < length else 0
        load += demand[node]
        if load > capacity + 1e-8:
            return math.inf
        arc = distance[previous, node]
        total += arc
        clock = max(clock + arc, windows[node, 0])
        if clock > windows[node, 1] + 1e-8:
            return math.inf
        clock += service[node]
        previous = node
    return total


@njit(cache=True)
def _batch(
    routes,
    lengths,
    costs,
    best,
    best_lengths,
    best_energy,
    distance,
    demand,
    windows,
    service,
    capacity,
    weight,
    temperature,
    steps,
    seed,
):
    if seed >= 0:
        np.random.seed(seed)
    slots, width = routes.shape
    energy = costs.sum() + weight * np.count_nonzero(lengths)
    accepted = 0
    for _ in range(steps):
        a = np.random.randint(slots)
        while lengths[a] == 0:
            a = np.random.randint(slots)
        b = np.random.randint(slots)
        na, nb = lengths[a], lengths[b]
        ra, rb = routes[a].copy(), routes[b].copy()
        move = np.random.randint(5)
        if move == 0 or move == 4:  # Relocate a customer or a short chain.
            size = min(na, np.random.randint(2, 4)) if move == 4 else 1
            start = np.random.randint(na - size + 1)
            if a == b:
                continue
            insertion = np.random.randint(nb + 1)
            for j in range(nb - 1, insertion - 1, -1):
                rb[j + size] = rb[j]
            for j in range(size):
                rb[insertion + j] = ra[start + j]
            for j in range(start, na - size):
                ra[j] = ra[j + size]
            na -= size
            nb += size
        elif move == 1:  # Swap customers.
            if nb == 0:
                continue
            i, j = np.random.randint(na), np.random.randint(nb)
            if a == b:
                ra[i], ra[j] = ra[j], ra[i]
            else:
                ra[i], rb[j] = rb[j], ra[i]
        elif move == 2:  # Reverse a segment (2-opt).
            b = a
            if na < 2:
                continue
            i, j = np.random.randint(na), np.random.randint(na)
            if i > j:
                i, j = j, i
            while i < j:
                ra[i], ra[j] = ra[j], ra[i]
                i += 1
                j -= 1
        else:  # Exchange route tails (2-opt-star), including route merges.
            if a == b:
                continue
            i, j = np.random.randint(na + 1), np.random.randint(nb + 1)
            new_na, new_nb = i + nb - j, j + na - i
            if max(new_na, new_nb) >= width:
                continue
            for k in range(nb - j):
                ra[i + k] = routes[b, j + k]
            for k in range(na - i):
                rb[j + k] = routes[a, i + k]
            na, nb = new_na, new_nb
        ca = _cost(ra, na, distance, demand, windows, service, capacity)
        if not math.isfinite(ca):
            continue
        delta = ca - costs[a] + weight * ((na > 0) - (lengths[a] > 0))
        cb = 0.0
        if a != b:
            cb = _cost(rb, nb, distance, demand, windows, service, capacity)
            if not math.isfinite(cb):
                continue
            delta += cb - costs[b] + weight * ((nb > 0) - (lengths[b] > 0))
        if delta <= 0 or np.random.random() < math.exp(-delta / temperature):
            routes[a] = ra
            lengths[a], costs[a] = na, ca
            if a != b:
                routes[b] = rb
                lengths[b], costs[b] = nb, cb
            energy += delta
            accepted += 1
            if energy < best_energy - 1e-8:
                best_energy = energy
                best[:, :] = routes
                best_lengths[:] = lengths
    return best_energy, accepted


def warmup():
    """Compile once on a synthetic instance, without benchmark input or references."""
    routes = np.array([[1, 0, 0], [0, 0, 0]], dtype=np.int64)
    lengths = np.array([1, 0], dtype=np.int64)
    distance = np.array([[0.0, 1.0], [1.0, 0.0]])
    demand = np.array([0.0, 1.0])
    windows = np.array([[0.0, 100.0], [0.0, 100.0]])
    service = np.zeros(2)
    _batch(
        routes,
        lengths,
        np.array([2.0, 0.0]),
        routes.copy(),
        lengths.copy(),
        2.0,
        distance,
        demand,
        windows,
        service,
        2.0,
        0.0,
        1.0,
        1,
        0,
    )


def anneal_static(
    p,
    initialize,
    validate,
    *,
    seed=0,
    initial=None,
    time_limit=20.0,
    initial_temperature_factor=0.005,
    final_temperature=0.02,
    max_iterations=None,
):
    """Run SA with cooling tied to elapsed time, including initialization."""
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    if not math.isfinite(initial_temperature_factor) or initial_temperature_factor <= 0:
        raise ValueError("initial_temperature_factor must be finite and positive")
    if not math.isfinite(final_temperature) or final_temperature <= 0:
        raise ValueError("final_temperature must be finite and positive")
    if max_iterations is not None and (
        not isinstance(max_iterations, (int, np.integer)) or max_iterations <= 0
    ):
        raise ValueError("max_iterations must be a positive integer or None")
    started = time.perf_counter()
    deadline = started + time_limit
    rng = np.random.default_rng(seed)
    initial_routes = initialize(p, rng, deadline) if initial is None else initial
    initial_metrics = validate(p, initial_routes)
    slots = min(p.max_vehicles, p.n)
    routes = np.zeros((slots, p.n + 1), dtype=np.int64)
    lengths = np.zeros(slots, dtype=np.int64)
    costs = np.zeros(slots)
    for i, route in enumerate(initial_routes):
        routes[i, : len(route)] = route
        lengths[i] = len(route)
        costs[i] = _cost(routes[i], len(route), p.distance, p.q, p.tw, p.service, p.capacity)
    weight = 2 * p.n * float(p.distance.max()) + 1 if p.mode == "benchmark" else 0.0
    best, best_lengths = routes.copy(), lengths.copy()
    best_energy = costs.sum() + weight * np.count_nonzero(lengths)
    initial_temperature = max(1.0, initial_metrics["distance"] * initial_temperature_factor)
    history = [(time.perf_counter() - started, initial_metrics["distance"], len(initial_routes))]
    history_iterations = [0]
    iterations = accepted = 0
    while time.perf_counter() < deadline:
        if max_iterations is not None and iterations >= max_iterations:
            break
        steps = 256 if max_iterations is None else min(256, max_iterations - iterations)
        progress = min(1.0, (time.perf_counter() - started) / time_limit)
        temperature = initial_temperature * (final_temperature / initial_temperature) ** progress
        old_best = best_energy
        best_energy, count = _batch(
            routes,
            lengths,
            costs,
            best,
            best_lengths,
            best_energy,
            p.distance,
            p.q,
            p.tw,
            p.service,
            p.capacity,
            weight,
            temperature,
            steps,
            seed if iterations == 0 else -1,
        )
        iterations += steps
        accepted += count
        if best_energy < old_best - 1e-8:
            vehicles = int(np.count_nonzero(best_lengths))
            history.append(
                (time.perf_counter() - started, best_energy - weight * vehicles, vehicles)
            )
            history_iterations.append(iterations)
    search_elapsed = time.perf_counter() - started
    result_routes = [best[i, :length].tolist() for i, length in enumerate(best_lengths) if length]
    metrics = validate(p, result_routes)
    return dict(
        routes=result_routes,
        metrics=metrics,
        initial=initial_metrics,
        seed=seed,
        elapsed=time.perf_counter() - started,
        search_elapsed=search_elapsed,
        time_limit=time_limit,
        stop_reason=(
            "iterations"
            if max_iterations is not None and iterations >= max_iterations
            else "time_limit"
        ),
        iterations=iterations,
        accepted=accepted,
        history=history,
        history_iterations=history_iterations,
        initial_routes=[list(r) for r in initial_routes],
    )
