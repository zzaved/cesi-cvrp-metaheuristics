"""CVRP and CVRPTW solver for the CesiCDP answer to the ADEME smart mobility call.

Node 0 is always the depot; customers are numbered 1..n. A solution is a list of
routes, each route a list of customer indices without the depot.
"""

from cvrp.instance import Instance
from cvrp.solution import Solution

__all__ = ["Instance", "Solution"]
__version__ = "0.1.0"
