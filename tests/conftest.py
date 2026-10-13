import numpy as np
import pytest

from cvrp import Instance


@pytest.fixture
def tiny() -> Instance:
    """Six customers on a small grid, Q = 10: small enough to check by hand."""
    coords = np.array([[0, 0], [1, 0], [2, 0], [0, 1], [0, 2], [-1, 0], [0, -1]], dtype=float)
    demands = np.array([0, 4, 4, 3, 3, 5, 5], dtype=float)
    return Instance(name="tiny", coords=coords, demands=demands, capacity=10, num_vehicles=3)


@pytest.fixture
def tiny_tw(tiny: Instance) -> Instance:
    """The tiny instance with wide windows and unit service times (none at the depot)."""
    n = tiny.n_customers + 1
    service = np.ones(n)
    service[0] = 0.0
    return Instance(
        name="tiny-tw",
        coords=tiny.coords,
        demands=tiny.demands,
        capacity=tiny.capacity,
        num_vehicles=3,
        ready_times=np.zeros(n),
        due_times=np.full(n, 100.0),
        service_times=service,
    )
