# Data

Benchmark instances are **downloaded, never committed** (`data/*` is git-ignored except this file).
Everything under `data/` is read by `experiments/run_benchmark.py` through the paths listed in
`experiments/config.yaml`.

## Expected layout

```
data/
  cvrplib/
    A/  A-n32-k5.vrp  A-n32-k5.sol  ...   Augerat set A (random customers), n = 31 to 79
    B/  B-n31-k5.vrp  ...                 Augerat set B (clustered customers)
    P/  P-n16-k8.vrp  ...                 Augerat set P (modified A and B)
    X/  X-n101-k25.vrp ...                Uchoa et al. (2017), n = 100 to 1000
  solomon/
    C101.txt  R101.txt  RC101.txt ...     Solomon (1987), CVRPTW, n = 100
  homberger/
    C1_2_1.txt ...                        Gehring and Homberger, CVRPTW, n = 200 to 1000
```

## Where to get them

| Set | Source | Format for `Instance.from_vrplib` |
| --- | --- | --- |
| Augerat A, B, P and Uchoa X | CVRPLIB, [galgos.inf.puc-rio.br/cvrplib](https://galgos.inf.puc-rio.br/cvrplib/) | `instance_format="vrplib"` |
| Solomon | SINTEF TOP, [sintef.no/projectweb/top/vrptw](https://www.sintef.no/projectweb/top/vrptw/) | `instance_format="solomon"` |
| Gehring and Homberger | same SINTEF page | `instance_format="solomon"` |

CVRPLIB moved in 2025 from `vrp.galgos.inf.puc-rio.br` to `galgos.inf.puc-rio.br/cvrplib`, and
the old direct file links now return 404.

### URLs used (16 October 2026)

Files needed by `notebooks/01_modeling_check.ipynb`:

| Files | URL |
| --- | --- |
| `cvrplib/P/*` (whole set P, `.7z`, extract with `bsdtar -xf P.7z`) | `https://galgos.inf.puc-rio.br/cvrplib/index.php/en/download/instance-set/12` |
| `cvrplib/A/A-n32-k5.{vrp,sol}` | `https://raw.githubusercontent.com/PyVRP/VRPLIB/main/tests/data/A-n32-k5.vrp` (and `.sol`) |
| `cvrplib/B/B-n31-k5.{vrp,sol}` | `https://raw.githubusercontent.com/PyVRP/VRPLIB/main/tests/data/B-n31-k5.vrp` (and `.sol`) |
| `solomon/*.{txt,sol}` (all 56) | `https://raw.githubusercontent.com/PyVRP/VRPLIB/main/tests/data/cvrplib/Vrp-Set-Solomon/<name>.txt` (and `.sol`) |

Other CVRPLIB sets follow the same pattern (`download/instance-set/<id>`: 4 is A, 5 is B, 9 is
E, 12 is P). The whole A and B sets are still to download for the experimental study.

Each `.vrp` should come with its `.sol` file (best known solution): its cost is used for the gap.
For Solomon instances, write the best known value in `config.yaml` (`best_known:`) and cite where it
comes from in `docs/content/experimentation/instances.md`.

## Conventions

- CVRPLIB `EUC_2D` distances are **rounded to the nearest integer** (`round_euc2d=True`), which is
  the convention under which the best known costs are published.
- Solomon: the loader keeps exact distances, but the best known costs of the PyVRP/VRPLIB copy
  (all 56 `.sol` files, checked on 7 November 2026) use distances **truncated to one decimal**
  (`distance_matrix(coords, rounding="floor1")`). Use that convention for every gap, otherwise
  each gap is about 0.3 % too high (C101: 828.94 exact, 827.3 truncated, same routes).
- Synthetic instances (`Instance.random`) need no download and are generated from a seed.

## SA notebook and supplied Solomon files

`notebooks/SA.ipynb` reads the supplied standard Solomon `.txt` files and their
accompanying `.sol` references from `data/solomon/`. The 56 pairs were copied from
the user's local Solomon collection; they remain git-ignored. Existing `.vrp`
copies are not used by this notebook. Input hashes are printed in its data cell.

For this dataset, both travel distance and travel time use Euclidean arcs truncated
to one decimal. All 56 references were independently checked for coverage,
capacity, time windows and fleet feasibility, and their recomputed distances match
the costs in the supplied `.sol` files. These are distance-oriented references,
not fleet-first solutions: the supplied R101 reference has 20 routes and cost
1637.7. This dataset-specific convention takes precedence over the generic exact
Solomon convention above when reproducing this comparison.

The notebook runs SA on all 56 supplied instances, without excluding tuning
instances or selecting a smaller subset. Seeds 0-9 and a 20-second budget give
560 SA runs. It displays all per-run iteration counts and per-instance means and
sample standard deviations. Results remain in memory; no CSV files are exported.
This is a full-dataset descriptive benchmark, not a held-out evaluation.

The shared implementation is in `src/cvrp/sa_vrptw.py` and `sa_static.py`;
`experiments/sa_adapter.py` imports the same construction and validation helpers.
Numba is a main dependency. Compilation is synthetic setup outside the measured
budget; construction and search are inside it, and reported elapsed time includes
final validation. SA counts proposed move attempts. The notebook runs SA only; elapsed time
reflects both the search strategy and its compiled implementation.

SA's initial-temperature factor 0.005 and final temperature 0.02 are fixed
exploratory heuristic settings, not values selected by a formal six-instance
temperature-tuning experiment. The notebook explains this limitation explicitly.
