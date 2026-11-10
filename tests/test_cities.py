"""Real-city loader (RRNCO files). Skipped when the city files are not downloaded."""

from pathlib import Path

import numpy as np
import pytest

from cvrp.cities import load_city

CITY_DIR = Path(__file__).resolve().parents[1] / "data" / "cities"
FILES = sorted(CITY_DIR.glob("*_data.npz"))
pytestmark = pytest.mark.skipif(not FILES, reason="no city file in data/cities/")


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_sizes_and_depot(path):
    full = load_city(path)
    assert full.n_customers == 999 and full.dist.shape == (1000, 1000)
    small = load_city(path, n=100, seed=3)
    assert small.n_customers == 100 and small.dist.shape == (101, 101)
    assert small.demands[0] == 0 and small.demands[1:].min() >= 1
    # same depot whatever the sample
    assert np.allclose(full.coords[0], small.coords[0])


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_reproducible_and_asymmetric(path):
    a, b = load_city(path, n=200, seed=1), load_city(path, n=200, seed=1)
    assert np.array_equal(a.dist, b.dist) and np.array_equal(a.demands, b.demands)
    assert not np.allclose(a.dist, a.dist.T)  # one-way streets


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_time_windows_reachable(path):
    inst = load_city(path, n=200, metric="duration", time_windows=True)
    assert inst.has_time_windows
    # each customer can be reached from the depot before its window closes, even at peak (x1.8)
    assert np.all(inst.ready_times[0] + 1.8 * inst.dist[0, 1:] <= inst.due_times[1:] + 1e-9)
    with pytest.raises(ValueError):
        load_city(path, n=10, metric="distance", time_windows=True)
