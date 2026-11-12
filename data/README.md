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
copies are not used by this notebook. The data cell checks every reference with the shared evaluator.

For this dataset, both travel distance and travel time use Euclidean arcs truncated
to one decimal. All 56 references were independently checked for coverage,
capacity, time windows and fleet feasibility, and their recomputed distances match
the costs in the supplied `.sol` files. These are distance-oriented references,
not fleet-first solutions: the supplied R101 reference has 20 routes and cost
1637.7. This dataset-specific convention takes precedence over the generic exact
Solomon convention above when reproducing this benchmark.

The SA notebook restores the original timed Solomon study: six tuning instances
(C101, C201, R101, R201, RC101, RC201), seeds 101-102 and twelve temperature
settings give 144 tuning runs. The selected setting is evaluated on the other
50 instances with seeds 1-10, giving 500 test runs. All use 20 seconds. These
already-executed outputs are restored from
`notebooks/archive/SA_before_single_seed_2026-11-12.ipynb`, not rerun or fabricated.
Means and sample standard deviations describe repeated seeds; class-level
intervals describe variation across instances. No CSV files are exported automatically.

The intervening one-seed, 10-million-move notebook is preserved in
`notebooks/archive/SA_before_homberger_budgets_2026-11-12.ipynb`. Its budget differs
from the timed campaigns, so its results must not be pooled with them.

The Homberger extension uses `R1_4_1`, `R1_8_1` and `R1_10_1` with seeds 1-3 at
20, 60 and 120 seconds: 27 runs. The `.vrp` files and matching `.sol` references
are stored in `data/homberger/`; `sources.json` records provenance and hashes.
Temperature parameters remain fixed at the setting selected by the original
Solomon tuning. Since cooling follows elapsed time, changing the budget also
changes cooling speed. Three seeds and one R1 instance per size support only a
small, descriptive comparison, not a general scaling or significance claim.

For Homberger, the notebook reports both gap to the feasible best-known reference
(an upper bound) and excess over a justified lower bound. The latter is the maximum
of the graph's MST cost and a capacity-aware depot-edge bound; it relaxes time
windows and can be weak. New runs record elapsed time, process CPU time, proposed
moves and batch-snapshot time to the final observed best. That observation is not
proof of convergence. The separate 10,000-customer synthetic section remains
untimed with seed 1 and ten million proposed moves.

The public solver is `sa(inst, SAParams(...), seed)` in `src/cvrp/sa.py`, returning
`SAResult(best, cost, runtime, iterations, history)` with a shared `Solution`.
The low-level implementation is in `sa_vrptw.py` and `sa_static.py`;
`experiments/sa_adapter.py` calls the same public solver as the notebook.
Numba is a main dependency. Compilation is synthetic setup outside measured
runtime; reported elapsed time includes construction, search and final validation.
SA counts proposed move attempts, including rejected and infeasible proposals.
With `time_limit=None`, temperature follows move count until the iteration budget
is complete. Numeric time limits cool according to elapsed time.
The notebook runs SA only; elapsed time
reflects both the search strategy and its compiled implementation.

SA's default factor 0.005 and final temperature 0.02 remain exploratory heuristics.
The matched tuning grid uses factors 0.0025/0.005/0.01 and final temperatures
0.005/0.01/0.02/0.05; defaults are not labelled as tuned before running selection.
Earlier development examined test cases, so the matched split does not establish
blind validation. The notebook performs no algorithm comparisons. It rejects incomplete, quick,
infeasible or differently seeded SA test records. Proposed-move counts and
observed runtime provide context for the compiled implementation.
