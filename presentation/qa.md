# Questions the jury will ask, and our answers

Built from the professor's review of 10 November and the rules in `.claude/agents/professor.md`.
Every answer points to a number in `results/` or a slide.

## Model

**Why did you change the objective?**
Version 1 minimized the sum of fixed arc times, so the hour of departure had no effect: it was the
textbook distance CVRP. The brief asks for the total route duration, and the ADEME call is about
traffic. Version 2 is one component, return time minus departure time per truck, with
c_ij^h = ρ_h c_ij. Traffic and waiting are inside z. (Slides 3 and 4.)

**Where does ρ_h come from?**
It is our assumption (peaks 1.75 to 1.80 at 7:00 to 9:00 and 17:00 to 19:00, 1.0 at night). The
model only reads the matrix, so measured speeds change no equation. We say it on slide 18.

**Is your model the one your code optimizes?**
Yes: `solve_tdvrptw` implements constraints (1) to (11) and matches the enumeration of every plan on
the toy instance (247.16 min). The metaheuristics take the route cost as a function:
`duration_cost` (Tabu) and `objective="duration"` (GRASP) compute the same z, and a test checks they
agree.

**The first in, first out property?**
Not guaranteed: the travel time depends on the departure hour only, so leaving at 8:59 can arrive
after leaving at 9:01. Accepted simplification; cutting each trip at the full hour removes it.

**Why big-M = 2880?**
Two days in minutes: larger than any |a_j − t_i − s_i − c_ij^h| in a working day, so the line is
inactive when the arc is unused. Its weakness is why the LP bound is useless with traffic.

## Complexity

**Which reduction, in which direction?**
Hamiltonian cycle ≤p our decision version: K = 1, wide windows, ρ = 1, arc cost 1/(m+1) on an edge
and 2/(m+1) otherwise, bound B = 1. Both directions are proven in section 2. The decision version is
in NP (certificate: routes and departures, checked in O(n + K)).

## Exact approach

**Up to which size is the ILP useful?**
With traffic: 7 to 8 customers in 60 s. With windows and no traffic: 100 customers on C101 and R101
(equal to the best known values), fewer than 50 on RC101. Without windows: capacity cuts and flow
solve every tested size up to 16; MTZ stops at 10 to 14.

## Metaheuristics

**Why GRASP-ILS?**
Rule fixed before the campaign: feasible on every run, then lowest mean gap, then time. On 50 test
instances times 10 seeds at 20 s: GRASP-ILS 1.16 %, SA 1.70 %, Tabu 3.98 %; Friedman p = 4e-13 and
every Wilcoxon pair significant after Holm.

**But Tabu wins in Paris and São Paulo. Is your choice wrong?**
No, it depends on the scenario, and that is our recommendation (slide 17). With time windows the
construction decides, and GRASP-ILS's regret insertion is the best start (it leads at every size up
to 1 000). Without windows on 999 real customers, what decides is the number of improving moves
per second: Tabu makes about 30 000 iterations in 60 s, GRASP-ILS one, and the control run shows
its kicks never start (0, 10 and 30 kicks give the same cost).

**Is the comparison fair? SA is compiled.**
Not perfectly, and we say it. Same machine, same evaluator, same wall clock budget, interleaved
jobs. Compilation favors SA, which still comes second on Solomon.

**How were the parameters chosen?**
Grid on 6 tuning instances never used in the test (9 to 12 settings each, 2 seeds). Then a one
factor at a time sensitivity study per algorithm, 3 seeds, around the tuned value (slide 16).

**What is the limit of each algorithm?** (the professor's own words)
- Tabu Search: the number of trucks with time windows. At 1 000 customers it uses about 60 % more
  trucks than GRASP-ILS and its moves rarely empty a route: 37 % gap at 1 000, 20 s. Without windows
  it is the best, up to 10 000 customers (18.6 % above a lower bound).
- SA: time. 6 times more time halves its gap at 1 000 customers (21.8 % to 10.5 %), the largest
  gain of the three; at 10 000 customers 14 million moves leave it 84 % above the lower bound.
- GRASP-ILS: time per iteration. At 800 customers and more, one construction plus descent takes the
  whole budget, so the multi-start and the kicks never happen.
- At 10 000 customers GRASP-ILS returns nothing: after 684 s its first iteration had not ended.

## Scale and real world

**Why Paris and São Paulo, not France and Egypt?**
The RRNCO dataset gives real road matrices (shortest paths on OpenStreetMap) for both cities with
the same area and the same number of customers. Cairo would need our own OSM extraction, which we
could not validate in time. We kept the protocol identical so the comparison is valid; Brazil is,
like Egypt, an emerging megacity with a less regular network (circuity 1.65 against 1.51).

**Why does one algorithm do better in one city?**
The ranking is the same in both cities (Tabu, GRASP-ILS, SA). São Paulo has longer, more circuitous
trips at a higher mean speed, which raises every cost but does not change which search is best.

**What happens at night?**
Same customers, same algorithm, departure at 22:00 instead of 08:00: the total duration drops by
about 45 % in Paris and 44 % in São Paulo, because ρ = 1 at night. The algorithms rank the same
(Tabu ahead of GRASP-ILS at both hours). Routes crossing midnight are handled (ρ repeats every 24 h).

**Without a best known value, how do you measure quality?**
Gap to the best run of all algorithms and seeds, and a minimum spanning tree lower bound for the
10 000 customer instance. Never against the initial solution.

## Statistics

**Why Friedman and Wilcoxon?**
Gaps are not normal and the same instances are used by all algorithms: paired, non parametric.
Holm corrects for three comparisons.

**How many seeds?**
10 on Solomon, 3 on Homberger and sensitivity, 5 on cities, 1 at 10 000 customers (memory: 800 MB
per run on an 8 GB laptop, so one run at a time).
