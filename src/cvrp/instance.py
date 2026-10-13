"""Problem data: the `Instance` dataclass and its loaders."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from cvrp.utils import distance_matrix, make_rng


@dataclass
class Instance:
    """A CVRP or CVRPTW instance.

    Node 0 is the depot. Arrays are indexed by node, so ``demands[0] == 0``.

    Attributes:
        name: Instance identifier, for example ``"X-n101-k25"``.
        coords: Node coordinates, shape (n + 1, 2).
        demands: Demand of each node, shape (n + 1,).
        capacity: Capacity Q shared by every vehicle (homogeneous fleet).
        num_vehicles: Fleet size k; ``None`` means unbounded.
        ready_times: Earliest service start e_i, or ``None`` for plain CVRP.
        due_times: Latest service start l_i, or ``None`` for plain CVRP.
        service_times: Service duration s_i at each node, or ``None``.
        best_known: Best known objective value, used for the gap.
        dist: Travel cost matrix, shape (n + 1, n + 1). Built from ``coords``
            when not given. In this project travel time equals distance
            (unit speed); see docs for the traffic extension.
    """

    name: str
    coords: np.ndarray
    demands: np.ndarray
    capacity: float
    num_vehicles: int | None = None
    ready_times: np.ndarray | None = None
    due_times: np.ndarray | None = None
    service_times: np.ndarray | None = None
    best_known: float | None = None
    dist: np.ndarray = field(default=None, repr=False)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Validate shapes and build the distance matrix if missing."""
        self.coords = np.asarray(self.coords, dtype=float)
        self.demands = np.asarray(self.demands, dtype=float)
        if self.coords.shape != (len(self.demands), 2):
            raise ValueError("coords must have shape (len(demands), 2)")
        if self.dist is None:
            self.dist = distance_matrix(self.coords)
        if self.demands.max() > self.capacity:
            raise ValueError("a customer demand exceeds the vehicle capacity")

    @property
    def n_customers(self) -> int:
        """Number of customers n (the depot is not counted)."""
        return len(self.demands) - 1

    @property
    def has_time_windows(self) -> bool:
        """Whether this is a CVRPTW instance."""
        return self.ready_times is not None and self.due_times is not None

    @property
    def lower_bound_vehicles(self) -> int:
        """Trivial bin packing bound: ceil(total demand / Q)."""
        return int(np.ceil(self.demands.sum() / self.capacity))

    @classmethod
    def from_vrplib(
        cls,
        path: str | Path,
        solution_path: str | Path | None = None,
        instance_format: str = "vrplib",
        round_euc2d: bool = True,
    ) -> Instance:
        """Load an instance from a VRPLIB or Solomon file with the `vrplib` package.

        Args:
            path: Path to the ``.vrp`` (CVRPLIB) or ``.txt`` (Solomon) file.
            solution_path: Optional ``.sol`` file; its cost becomes ``best_known``.
            instance_format: ``"vrplib"`` or ``"solomon"``.
            round_euc2d: Round ``EUC_2D`` distances to the nearest integer, the
                CVRPLIB convention under which best known costs are reported.

        Returns:
            The parsed instance, with the depot moved to index 0.
        """
        import vrplib  # imported lazily so the core does not need it for tests

        data = vrplib.read_instance(str(path), instance_format=instance_format)
        depot = int(np.atleast_1d(data.get("depot", [0]))[0])
        if depot != 0:
            # TODO(Person 3): reorder nodes so the depot is node 0.
            raise NotImplementedError("depot must be node 0")

        best = None
        if solution_path is not None:
            best = float(vrplib.read_solution(str(solution_path))["cost"])

        dist = np.asarray(data["edge_weight"], dtype=float) if "edge_weight" in data else None
        if dist is not None and round_euc2d and data.get("edge_weight_type") == "EUC_2D":
            dist = np.rint(dist)

        tw = data.get("time_window")
        return cls(
            name=str(data.get("name", Path(path).stem)),
            coords=data["node_coord"],
            demands=data["demand"],
            capacity=float(data["capacity"]),
            num_vehicles=_parse_vehicles(data),
            ready_times=None if tw is None else np.asarray(tw)[:, 0].astype(float),
            due_times=None if tw is None else np.asarray(tw)[:, 1].astype(float),
            service_times=_as_array(data.get("service_time"), len(data["demand"])),
            best_known=best,
            dist=dist,
        )

    @classmethod
    def random(
        cls,
        n: int,
        capacity: float = 100.0,
        seed: int | None = 0,
        distribution: str = "uniform",
        name: str | None = None,
    ) -> Instance:
        """Generate a synthetic CVRP instance for quick tests and scenarios.

        Args:
            n: Number of customers.
            capacity: Vehicle capacity Q.
            seed: Random seed.
            distribution: ``"uniform"`` (R-type) or ``"clustered"`` (C-type).
            name: Optional name; a descriptive one is built otherwise.
        """
        rng = make_rng(seed)
        if distribution == "uniform":
            pts = rng.uniform(0, 100, size=(n, 2))
        elif distribution == "clustered":
            centers = rng.uniform(10, 90, size=(max(2, n // 20), 2))
            labels = rng.integers(len(centers), size=n)
            pts = centers[labels] + rng.normal(0, 4, size=(n, 2))
        else:
            # TODO(Person 3): add "mixed" (RC-type) and "real-city" scenarios.
            raise ValueError(f"unknown distribution {distribution!r}")
        coords = np.vstack([[50.0, 50.0], pts])
        demands = np.concatenate([[0.0], rng.integers(1, 11, size=n).astype(float)])
        return cls(
            name=name or f"rand-{distribution}-n{n}-s{seed}",
            coords=coords,
            demands=demands,
            capacity=capacity,
        )


def _parse_vehicles(data: dict) -> int | None:
    """Read the fleet size from a vrplib dict, if the file states it."""
    for key in ("vehicles", "vehicle"):
        if key in data:
            return int(np.atleast_1d(data[key])[0])
    name = str(data.get("name", ""))
    if "-k" in name:  # CVRPLIB naming convention: X-n101-k25
        try:
            return int(name.rsplit("-k", 1)[1])
        except ValueError:
            return None
    return None


def _as_array(value: object, size: int) -> np.ndarray | None:
    """Broadcast a scalar or array field to one value per node."""
    if value is None:
        return None
    arr = np.asarray(value, dtype=float)
    return np.full(size, float(arr)) if arr.ndim == 0 else arr
