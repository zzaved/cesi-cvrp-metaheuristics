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

## Real cities (RRNCO, road network)

```
data/
  cities/
    Paris_data.npz  Sao_Paulo_data.npz      RRNCO dataset, 1,000 real points per city
```

Download `dataset/<City>/<City>_data.npz` from
[huggingface.co/datasets/ai4co/rrnco](https://huggingface.co/datasets/ai4co/rrnco) (16 MB each) and
rename it `<City>_data.npz`. Source: Son et al., *RRNCO*, ICLR 2026. Each file has `points`
(1000 x 2, lat, lon), `distance` (road km) and `duration` (free-flow minutes), both computed with
OSRM on OpenStreetMap and **asymmetric** (one-way streets). Load with `cvrp.cities.load_city`,
which adds the depot (road medoid), demands (1 to 10), capacity and optional time windows:

```python
from cvrp.cities import load_city
inst = load_city("data/cities/Paris_data.npz", n=1000)                       # km, up to 999 customers
inst = load_city("data/cities/Paris_data.npz", n=1000, metric="duration")    # minutes, for traffic mode
```

Lyon and Cairo are not in RRNCO. The file named `Alexandria` is Alessandria (Italy, 44.8 N
8.7 E), not Alexandria (Egypt): do not use it as an Egyptian city. Paris (France) and São Paulo
(congested megacity, also covered by the Uber speed data of the time-dependent benchmark of
Blauth et al. 2022) are used instead.

## Conventions

- CVRPLIB `EUC_2D` distances are **rounded to the nearest integer** (`round_euc2d=True`), which is
  the convention under which the best known costs are published.
- Solomon: the loader keeps exact distances, but the best known costs of the PyVRP/VRPLIB copy
  (all 56 `.sol` files, checked on 7 November 2026) use distances **truncated to one decimal**
  (`distance_matrix(coords, rounding="floor1")`). Use that convention for every gap, otherwise
  each gap is about 0.3 % too high (C101: 828.94 exact, 827.3 truncated, same routes).
- Synthetic instances (`Instance.random`) need no download and are generated from a seed.
