---
sidebar_position: 2
title: Experimental design
---

# Experimental design

Owner: **Person 3**. Methodology and statistics must be rigorously justified: this page is the
justification. Implementation: `experiments/run_benchmark.py`, `experiments/analyze.py`,
`notebooks/03_experimental_study.ipynb`.

## Research questions

| # | Question | Answered by |
| --- | --- | --- |
| RQ1 | How far is ALNS from the best known solutions, and does it stay under 7 percent? | gap per instance and per family |
| RQ2 | Does ALNS beat the simpler methods (NN, NN + local search, plain SA) significantly? | paired tests across instances |
| RQ3 | How does running time grow with n? | log-log fit of time against n |
| RQ4 | How do customer distribution, capacity tightness and time windows affect quality? | gap grouped by factor |
| RQ5 | Up to which n is the exact ILP usable, and how close are our solutions to its bounds? | exact study (Person 1) |

## Factors and levels

| Factor | Levels |
| --- | --- |
| Algorithm | NN, NN + LS, SA, ALNS (default parameters), ALNS variants if time allows |
| Instance size n | 15 to 80, 100 to 300, 500 to 1000, 2000 plus |
| Customer distribution | uniform (R), clustered (C), mixed (RC) |
| Constraint | capacity only (CVRP), capacity and time windows (CVRPTW) |
| Seed | 10 seeds per stochastic (algorithm, instance) pair; 1 for deterministic ones |

## Response variables (metrics)

| Metric | Definition |
| --- | --- |
| Cost | total travel time of the returned solution |
| Gap | $\text{gap}(\%) = 100 \cdot \dfrac{\text{cost}_{ours} - \text{cost}_{best\ known}}{\text{cost}_{best\ known}}$ |
| Time | wall-clock seconds, single thread |
| Routes | number of trucks used |
| Feasible | whether `Solution.violations` is empty (must be 100 percent) |
| Robustness | standard deviation and range of cost over seeds |

## Time budget

Same budget for every algorithm on a given instance, so comparisons are fair. Proposal:
$T(n) = \min(0.12\, n,\ 300)$ seconds (12 s for n = 100, 120 s for n = 1000). *To decide at
kickoff, depending on how much compute time the campaign can use:* 26 instances times 10 seeds
times 2 stochastic algorithms is about 520 runs.

## Statistical tests

1. **Unit of analysis:** the instance. For each (instance, algorithm), take the mean cost over
   seeds. Seeds measure robustness; instances are the independent samples.
2. **Two algorithms:** Wilcoxon signed-rank test on paired per-instance values.
   $H_0$: the median difference is zero. Non-parametric because gaps are not normally distributed.
3. **Three or more algorithms:** Friedman test on ranks, then pairwise post-hoc (Nemenyi, or
   Wilcoxon with Holm correction) as recommended by Demsar (2006).
4. **Significance level** $\alpha = 0.05$; report p-values and an effect size (median gap
   difference), not just "significant".
5. **Scaling:** fit $\log(\text{time}) = b \log(n) + a$; $b$ is the empirical exponent, compared
   with the theoretical complexity per iteration.

## Reproducibility

- Seeds listed in `config.yaml`; every run writes its seed in the CSV.
- Record hardware (CPU, RAM), Python and package versions with each campaign.
- Tuning instances are disjoint from test instances.
- Results CSVs are regenerated, never edited by hand.

## Threats to validity (to discuss in the deliverable)

- Best known values computed under a different rounding or objective (Solomon).
- Time limits differ from those in the literature, so gaps are not directly comparable to
  published methods.
- Parameters tuned on few instances may overfit.
- Synthetic instances may not reflect real road networks.
