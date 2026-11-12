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

## How each algorithm is built (anyone may be asked any of these)

The professor may ask any of us about any algorithm. These answers come from the code in
`src/cvrp/` and are the same for the three of us.

### Shared ground

**What do the three algorithms have in common?**
Same instance object (`Instance`), same encoding (a list of routes, depot implicit at both ends),
same final check (`Solution.violations`: capacity, windows, every customer once), same wall clock
budget, same machine. Each one keeps only feasible solutions: an infeasible route costs infinity,
so it is never accepted.

**What is a granular neighborhood?** (used by Tabu and GRASP-ILS)
A move of customer c is only tried next to one of c's k nearest customers (Toth and Vigo, 2003).
Good routes rarely connect far customers, so this cuts the neighborhood from O(n²) to O(n k)
almost without losing quality. k = 15 for Tabu, 20 for GRASP-ILS (both checked in the
sensitivity study).

**Which moves exist?**
- relocate: move one customer to another place.
- swap: exchange two customers.
- 2-opt: reverse a segment inside one route.
- 2-opt*: exchange the tails of two routes. It is the move that can empty a route.
- Or-opt: move a chain of 2 to 3 customers. GRASP-ILS uses it, and SA's chain relocate does the
  same job.

### Tabu Search (Pablo, `src/cvrp/tabu.py`)

**How does one iteration work?**
Sample 200 granular moves (relocate, swap, 2-opt*, 2-opt) around random customers and compute each
delta. Only the two routes a move touches are re-evaluated, and their costs are cached. Then
apply the best move that is not tabu, **even if it makes the plan worse**: accepting worse moves
is how Tabu Search climbs out of a local optimum.

**What is tabu, and for how long?**
The customers a move touched: they cannot move again for a tenure drawn at random in
[tenure / 2, 3 tenure / 2] iterations (tuned tenure 20, so 10 to 30). The random draw avoids
cycles of a fixed length.

**Aspiration criterion?**
A tabu move is allowed if it gives a new best solution.

**Initial solution?**
The time oriented nearest neighbor (Solomon, 1987): extend the route with the closest customer
that keeps it feasible, and open a new route when none fits.

**Stopping rule?** The time limit. The best plan seen is returned.

**Why a sampled candidate list instead of the full neighborhood?**
With 1 000 customers the full neighborhood has millions of moves. 200 samples keep one iteration
at about 1 to 2 ms at any n, which is why Tabu still works at 10 000 customers. The sensitivity
study shows the trade off: 25 candidates make the step almost random (20 % gap), 800 make it
14 times slower (7.9 %).

**Its weakness?**
The nearest neighbor start opens too many routes with windows, and relocate and swap rarely
empty a route. At 1 000 customers it uses 171 trucks against 106.

**How does it handle traffic?**
Only the route cost changes: `duration_cost` simulates the route with the hourly factor ρ_h and
returns arrival at the depot minus departure. The search itself does not change.

### GRASP-ILS (Farida, `src/cvrp/grasp.py`)

**What does GRASP stand for, and what is one iteration?**
Greedy Randomized Adaptive Search Procedure (Feo and Resende, 1995). One iteration is a
randomized greedy construction, a local search, then 90 kicks (the ILS part). The best feasible
plan over all iterations is returned.

**How does the construction work?**
Parallel insertion. For each unrouted customer the cheapest feasible insertion over all open
routes is kept up to date (only the route that changed is recomputed). The score is the
**regret**: insertion cost minus (second best route minus best route), so customers with few good
options are served first. The restricted candidate list (RCL) keeps the customers with
score ≤ s_min + α (s_max − s_min), and one of them is drawn at random. α = 0 is pure greedy and
α = 1 is pure random. Tuned α = 0.3. When no customer fits, a new route opens with a seed
customer (far from the depot or with an early due date).

**Why is it the best with time windows?**
The regret construction already gives few trucks and a good order. Windows make that start
decisive, and the descent cannot easily remove a truck later.

**Local search?**
Variable Neighborhood Descent with first improvement: relocate, then swap, 2-opt*, Or-opt and
intra-route 2-opt, all granular. After an improvement it restarts from the first neighborhood.

**How is feasibility checked so fast?**
Each route stores its arrival times A (forward pass) and its latest feasible start times Z
(backward pass, Savelsbergh 1992). A move is feasible if the new arrival at the next customer is
at most its Z, so most moves are checked in O(1) without simulating the route again.

**What is a kick?**
Remove a cluster of 10 to 20 % of the customers (a random customer and its neighbors), reinsert
them greedily (tight windows first), descend again, and keep the result only if it is better.
Without kicks (plain GRASP) the gap doubles: 2.50 % against 1.34 %.

**What if the construction uses more trucks than allowed?**
`_eliminate_routes` empties the smallest routes and reinserts their customers.

**Its weakness?**
Time per iteration. One construction plus descent takes about 60 s at 2 000 customers, and more
than 684 s at 10 000. The clock is read only between iterations and kicks (a defect, see above).

### Simulated Annealing (Dag, `src/cvrp/sa_static.py`, `src/cvrp/sa_vrptw.py`)

**How does one step work?**
Pick two random routes and one of five moves: relocate a customer, relocate a chain of 2 to 3
customers, swap, 2-opt inside a route, or 2-opt* between two routes (which can merge routes).
Compute the delta on the two routes. An infeasible result is rejected. Otherwise accept if
delta ≤ 0, or with probability exp(−delta / T) (Metropolis rule).

**Cooling schedule?**
Exponential in elapsed time: T(t) = T0 (Tf / T0)^(t / budget), with T0 = 0.01 × the cost of the
initial plan and Tf = 0.005 (tuned). It reaches Tf exactly at the end of the budget, so the same
schedule fits any time limit.

**Initial solution?**
Randomized cheapest feasible insertion: customers in random order, usually inserted at the best
place, sometimes (10 %) among the 3 best for diversity.

**Why is it compiled?**
The move loop runs in Numba (`@njit`), in batches of 256 moves. Compilation is a warm-up outside
the timer. That is why it makes about 16 million moves in 20 s at 1 000 customers.

**Why is it the most robust?**
Its gap stays between 0.55 and 0.83 % over a wide range of temperatures. It only breaks when T0
goes to 0 (factor 0.0005, 2.13 %): then it accepts almost no worse move and becomes a plain
descent.

**Its weakness?**
It needs a number of moves proportional to n. At 10 000 customers, 14 million moves are only
1 400 per customer, so the cooling ends before the plan is good (84 % above the bound).

### Questions that cross the three

**Exploration versus exploitation in each one?**
- Tabu Search: explores by accepting the best non-tabu move even if it is worse, and exploits
  with the best move of the sample and aspiration.
- SA: explores at high temperature and exploits at low temperature.
- GRASP-ILS: explores with the random RCL and the kicks, and exploits with the descent.

**Which one is deterministic?**
None. All three use a seed, and the same seed gives the same result. That is why every result is
a mean over seeds.

**Why does SA accept worse moves at random, but Tabu Search does it deterministically?**
SA draws the acceptance with exp(−delta / T). Tabu Search always takes the best allowed move, and
its memory (the tabu list) prevents going back. These are two ways to leave a local optimum.

**Which one would you combine, and how?**
GRASP-ILS's regret construction as the start of Tabu Search. It would fix Tabu's truck problem
with windows and keep its cheap iterations at large n. This is in the future work (section 10).

## General project questions (anyone may be asked)

**What problem do you solve, in one sentence?**
A capacitated vehicle routing problem with time windows and hourly traffic (TDVRPTW), minimizing
the total route duration of the fleet.

**What is a feasible solution?**
Every customer served exactly once, each route starts and ends at the depot, the load is at most
Q, the service starts inside [a_i, b_i] (waiting is allowed), and there are at most K trucks.

**Decision variables of the ILP?**
x_ij^k ∈ {0,1}: truck k drives from i to j. y_ih ∈ {0,1}: customer i is left during hour h (and
y_0h^k for the depot departure of truck k). t_i: service start at i, bounded by its window. t_0^k and
t_{n+1}^k: departure from and return to the depot of truck k (the depot is split into nodes 0 and
n + 1). Objective: Σ_k (t_{n+1}^k − t_0^k).

**Why is the problem NP-hard, in simple words?**
With one truck, no capacity limit and wide windows, it is already the travelling salesman
problem, and that is NP-hard. Our problem contains it.

**What is the gap, and against what?**
(cost − reference) / reference. The reference is the best known value on Solomon and Homberger,
the best plan over all our runs for the cities, and the radial lower bound at 10 000 customers.

**Why 20 s per run?**
It is the same budget for every algorithm, so the comparison is fair. 1 500 test runs fit in one
night. Round 2 adds 60 s, 120 s and 300 s to measure the effect of time.

**Tuning set and test set?**
6 Solomon instances for tuning, and the 50 other instances for the test, never seen during
tuning. This avoids overfitting the parameters.

**What did each of you build?**
- Pablo: the model, the complexity proof, the ILP and Tabu Search.
- Dag: Simulated Annealing.
- Farida: GRASP-ILS.
- All three: the shared evaluator and protocol.

**What would you do with more time?**
- Real measured traffic speeds instead of the assumed ρ_h.
- A test with routes that span several hours.
- A GRASP-ILS clock inside the construction.
- A regret start for Tabu Search.
- Retuning with tenure 35 and α 0.7.
- More seeds at 10 000 customers.
