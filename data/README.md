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

Status: **to verify**. CVRPLIB moved in 2025 from `vrp.galgos.inf.puc-rio.br` to
`galgos.inf.puc-rio.br/cvrplib`, and the old direct file links now return 404. Download from the
website, place the files as above, and record here the exact URL you used.

Each `.vrp` should come with its `.sol` file (best known solution): its cost is used for the gap.
For Solomon instances, write the best known value in `config.yaml` (`best_known:`) and cite where it
comes from in `docs/content/experimentation/instances.md`.

## Conventions

- CVRPLIB `EUC_2D` distances are **rounded to the nearest integer** (`round_euc2d=True`), which is
  the convention under which the best known costs are published.
- Solomon distances are kept exact (no rounding). Check that the best known values you compare
  against use the same convention, otherwise the gap is meaningless.
- Synthetic instances (`Instance.random`) need no download and are generated from a seed.
