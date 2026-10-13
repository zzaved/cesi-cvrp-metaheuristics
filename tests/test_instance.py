import numpy as np
import pytest

from cvrp import Instance
from cvrp.utils import distance_matrix, gap_percent


def test_distance_matrix_is_symmetric_with_zero_diagonal():
    d = distance_matrix(np.array([[0, 0], [3, 4], [6, 8]], dtype=float))
    assert d[0, 1] == pytest.approx(5.0)
    assert np.allclose(d, d.T)
    assert np.allclose(np.diag(d), 0)


def test_rounding_conventions():
    pts = np.array([[0, 0], [1, 1]], dtype=float)
    assert distance_matrix(pts, "nint")[0, 1] == 1.0
    assert distance_matrix(pts, "floor1")[0, 1] == pytest.approx(1.4)


def test_instance_properties(tiny: Instance):
    assert tiny.n_customers == 6
    assert not tiny.has_time_windows
    assert tiny.lower_bound_vehicles == 3
    assert tiny.dist.shape == (7, 7)


def test_demand_above_capacity_is_rejected():
    with pytest.raises(ValueError):
        Instance("bad", np.zeros((2, 2)), np.array([0, 20.0]), capacity=10)


@pytest.mark.parametrize("dist", ["uniform", "clustered"])
def test_random_instances_are_reproducible(dist: str):
    a = Instance.random(30, seed=1, distribution=dist)
    b = Instance.random(30, seed=1, distribution=dist)
    assert np.array_equal(a.coords, b.coords)
    assert a.n_customers == 30


def test_gap():
    assert gap_percent(107.0, 100.0) == pytest.approx(7.0)


VRP_FILE = """NAME : t-n4-k2
TYPE : CVRP
DIMENSION : 4
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 10
NODE_COORD_SECTION
1 0 0
2 1 1
3 3 4
4 0 2
DEMAND_SECTION
1 0
2 3
3 4
4 5
DEPOT_SECTION
1
-1
EOF
"""


def test_vrplib_loader_rounds_euc2d(tmp_path):
    path = tmp_path / "t-n4-k2.vrp"
    path.write_text(VRP_FILE)
    inst = Instance.from_vrplib(path)
    assert inst.n_customers == 3
    assert inst.num_vehicles == 2
    assert inst.dist[0, 1] == 1.0  # sqrt(2) rounded
    assert inst.dist[0, 2] == 5.0
