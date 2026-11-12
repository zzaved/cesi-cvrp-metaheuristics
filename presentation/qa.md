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
its kicks never start (0, 10 and 30 kicks give the same cost). Against the best plan found (Tabu,
300 s), Tabu at 60 s is 6 to 7 % above, GRASP-ILS 15 to 17 %, SA 29 to 34 %.

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
44 % in both cities. We say it first: that is 1 − 1/ρ(8) = 1 − 1/1.80. The routes last 32 min on
average, only 1 of 57 changes hour and none crosses midnight, so every trip is priced at one ρ. The
night measures the size of the traffic effect; the algorithms do not plan differently and rank the
same. A test where the order of visits must change needs routes spanning several hours (service
times and windows over a day); the model and the solvers support it, this experiment does not
exercise it.

**Without a best known value, how do you measure quality?**
Gap to the best plan of all runs (all algorithms, seeds and budgets), and the radial lower bound
2 Σ d_0i q_i / Q for the 10 000 customer instance: a route costs at least twice its farthest
customer's distance, and its load is at most Q. Never against the initial solution.

## Statistics

**Why Friedman and Wilcoxon?**
Gaps are not normal and the same instances are used by all algorithms: paired, non parametric.
Holm corrects for three comparisons.

**How many seeds?**
10 on Solomon, 3 on Homberger and sensitivity, 5 on cities, 1 at 10 000 customers (memory: 800 MB
per run on an 8 GB laptop, so one run at a time).

## Questions raised by our own strict review

**Your 300 s runs beat your best run. What are the real gaps in Paris?**
Against the best of all runs (Tabu, 300 s, 314.8 km): Tabu at 60 s 6.4 %, GRASP-ILS 14.7 %, SA
33.6 %; São Paulo 7.3 %, 16.7 %, 28.9 %.

**Where exactly does GRASP-ILS stop returning a plan?**
Without windows, budget 60 s: it finishes one iteration in 60 s at 1 000 and 2 000 customers, in
125 s at 5 000 (twice the budget), and had not finished after 684 s at 10 000. So it stops meeting
its budget between 2 000 and 5 000, and stops returning a plan at all between 5 000 and 10 000. Its
iteration time grows faster than n². Tabu Search: 0.7 ms per iteration at 1 000, 2.1 ms at 10 000.

**The sensitivity shows tenure 35 and α 0.7 are better. Why not retune?**
The test campaign was fixed with the tuned values before the study. The gains (0.6 and 0.3 points
on the tuning set) would not change the ranking of section 8: GRASP-ILS would gain, Tabu Search
would stay third. Retuning means rerunning the 1 500 test runs; it is in section 10.

**Tabu wins at 10 000 without windows. Would it win at 10 000 with windows?**
Not tested, and we say so. With windows it already fails on trucks at 1 000 (171 against 106), so we
would expect GRASP-ILS's construction to matter, if it can be made to finish (compiled).

**Same ρ in Paris and São Paulo: what is country specific?**
Only the road network geometry (trip length, circuity, asymmetry). The traffic profile is the same
assumption in both, so no traffic conclusion is country specific. Density, degree and one way share
need the graphs, which the RRNCO matrices do not include.

**Your solver ran 684 s on a 300 s budget. Acceptable?**
No. GRASP-ILS reads its clock only between iterations and kicks; at 10 000 customers one iteration is
longer than the budget. It is a defect of our implementation, fixed by checking the time inside the
construction and the descent and returning the best partial plan completed by a greedy insertion.
