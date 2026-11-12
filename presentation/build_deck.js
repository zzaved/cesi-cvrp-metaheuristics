// Final presentation, generated from presentation/data/summary.json and presentation/img/.
//   python presentation/summary.py && python presentation/figures.py render && node presentation/build_deck.js
// Every number on a slide comes from summary.json (results/ of the experiments). No code on slides.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const S = JSON.parse(fs.readFileSync(path.join(HERE, "data", "summary.json"), "utf8"));
const IMG = (f) => path.join(HERE, "img", f);
const has = (f) => fs.existsSync(IMG(f));
const OUT = path.join(HERE, "cvrp_final_presentation.pptx");

// ------------------------------------------------------------------ palette (Ink on Cream)
const K = {
  cream: "F4F0E5", creamDeep: "EBE5D6", navy: "1B2B6B", cobalt: "2547C9", verm: "C0391B",
  soft: "5A679E", ochre: "C98B1E", white: "FFFFFF", paleBlue: "DCE3F7",
};
const ALG = {
  grasp: { name: "GRASP-ILS", color: K.cobalt, who: "Farida" },
  sa: { name: "Simulated Annealing", color: K.verm, who: "Dag" },
  tabu: { name: "Tabu Search", color: K.ochre, who: "Pablo" },
};
const ORDER = ["grasp", "sa", "tabu"];
const THEME = {
  name: "Ink on Cream", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: K.navy, lt1: K.white, dk2: K.navy, lt2: K.cream, accent1: K.cobalt,
    accent2: K.verm, accent3: K.ochre, accent4: K.soft, accent5: K.creamDeep, accent6: "3F8F6B",
    hlink: K.cobalt, folHlink: K.soft },
};
const W = 13.333, H = 7.5, MX = 0.6;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Delivery routes with hourly traffic: CVRP and CVRPTW";
pres.author = "CesiCDP: Pablo, Dag, Farida";

// ------------------------------------------------------------------ layouts
const footer = (color) => ([
  { text: { text: "CesiCDP for ADEME   |   CVRP and CVRPTW with hourly traffic",
    options: { x: MX, y: H - 0.42, w: 8, h: 0.3, fontSize: 10, color, fontFace: "Calibri", margin: 0 } } },
]);
pres.defineSlideMaster({
  title: "CONTENT", background: { color: K.cream },
  objects: [
    ...footer(K.soft),
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.38, w: W - 2 * MX, h: 0.95,
      fontFace: "Cambria", fontSize: 28, bold: true, color: K.navy, valign: "top", align: "left", margin: 0 },
      text: "" } },
  ],
  slideNumber: { x: W - 1.1, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 10, color: K.soft, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK", background: { color: K.navy },
  objects: [...footer("AEB8E6")],
  slideNumber: { x: W - 1.1, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 10, color: "AEB8E6", align: "right" },
});

// ------------------------------------------------------------------ helpers
const T = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, fontFace: "Calibri",
  color: K.navy, fontSize: 16, valign: "top", ...o });
const kicker = (slide, text, color = K.verm) => T(slide, text.toUpperCase(),
  { x: MX, y: 0.12, w: 8, h: 0.26, fontSize: 11, bold: true, color, charSpacing: 3 });
const card = (slide, x, y, w, h, fill = K.white) => slide.addShape(pres.shapes.ROUNDED_RECTANGLE,
  { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08,
    shadow: { type: "outer", color: "000000", opacity: 0.08, blur: 6, offset: 2, angle: 90 } });
const stat = (slide, x, y, w, big, label, color = K.cobalt, size = 44) => {
  T(slide, big, { x, y, w, h: 0.8, fontFace: "Cambria", fontSize: size, bold: true, color });
  T(slide, label, { x, y: y + 0.82, w, h: 0.7, fontSize: 14, color: K.soft });
};
const pill = (slide, x, y, text, color) => {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 0.22, h: 0.22, fill: { color },
    line: { color }, rectRadius: 0.11 });
  T(slide, text, { x: x + 0.32, y: y - 0.04, w: 3.5, h: 0.3, fontSize: 14, bold: true });
};
const addGif = (slide, file, x, y, w, ratio, alt) => {
  if (!has(file)) { T(slide, `[${file} not rendered]`, { x, y, w, h: 0.5, color: K.verm }); return; }
  slide.addImage({ path: IMG(file), x, y, w, h: w * ratio, altText: alt });
};
const content = (title, section) => {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
};
const chartText = { catAxisLabelColor: K.soft, valAxisLabelColor: K.soft, catAxisLabelFontFace: "+mn-lt",
  valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11, dataLabelColor: K.navy,
  legendFontFace: "+mn-lt", legendFontSize: 12, legendColor: K.navy,
  valGridLine: { color: "D9D3C3", size: 0.5 }, catGridLine: { style: "none" },
  titleFontFace: "+mn-lt", titleColor: K.navy, titleFontSize: 14 };
const pct = (v, k = 1) => (v === null || v === undefined ? "n/a" : `${Number(v).toFixed(k)} %`);
const fmt = (v, k = 0) => Number(v).toLocaleString("en-US", { maximumFractionDigits: k, minimumFractionDigits: k });

// numbers used on several slides
const sol = S.solomon.overall;
const hom = (a, n, t) => S.homberger.rows.find((r) => r.algorithm === a && r.n === n && r.time_limit === t);
const city = (c, o, a) => S.cities.costs.find((r) => r.city === c && r.objective === o && r.algorithm === a);
const night = (c) => {
  const d = city(c, "duration 08:00", "tabu").mean, n = city(c, "duration 22:00", "tabu").mean;
  return { day: d, night: n, cut: 100 * (1 - n / d) };
};

// best plan of all distance runs in a city (60 s means and 300 s control means; see summary.py)
const bestAll = (c) => Math.min(...S.cities.costs.filter((r) => r.city === c && r.objective === "distance").map((r) => r.best),
  ...S.cities.control.filter((r) => r.city === c).map((r) => r.best));

// ================================================================== 1. title
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
  T(s, "CESI  |  ALGORITHMS AND COMBINATORIAL OPTIMIZATION  |  ADEME CALL", { x: MX, y: 0.7, w: 11, h: 0.3,
    fontSize: 12, bold: true, color: "AEB8E6", charSpacing: 2 });
  T(s, "Routing deliveries when the clock matters", { x: MX, y: 1.25, w: 6.1, h: 2.2, fontFace: "Cambria",
    fontSize: 44, bold: true, color: K.white });
  T(s, "From a model with hourly traffic to three metaheuristics tested from 100 to 10 000 customers and on real city road networks",
    { x: MX, y: 3.55, w: 5.9, h: 1.2, fontSize: 18, color: "DCE3F7" });
  T(s, "Pablo  ·  Dag  ·  Farida\n13 November 2026", { x: MX, y: 5.3, w: 5, h: 0.9, fontSize: 16, color: K.white });
  addGif(s, "race_rc101.gif", 6.85, 1.15, 6.1, 5.2 / 13.5,
    "Animation: Tabu Search, Simulated Annealing and GRASP-ILS improving their routes on Solomon RC101");
  T(s, "Live from our solvers: same instance, same 20 s", { x: 6.85, y: 3.65, w: 6.1, h: 0.3, fontSize: 12,
    italic: true, color: "AEB8E6", align: "right" });
  s.addNotes("Pablo opens. One sentence: we plan the routes of delivery trucks so that the total time on the road is as small as possible, with traffic that changes by the hour. The animation on the right is not a drawing: it is three of our solvers searching on the same instance.");
}

// ================================================================== 2. the question
{
  const s = content("One depot, a fleet, customers with windows, and traffic that changes every hour", "Opening");
  kicker(s, "The question");
  card(s, MX, 1.6, 5.6, 4.9, K.navy);
  T(s, "“Which truck serves which customers, in which order, and when does it leave, so that the total route duration is minimal?”",
    { x: MX + 0.4, y: 1.95, w: 4.8, h: 2.6, fontFace: "Cambria", fontSize: 24, italic: true, color: K.white });
  T(s, "Level B: CVRP (capacity)\nLevel A: CVRPTW (capacity and time windows)\nOur extension: hourly traffic",
    { x: MX + 0.4, y: 4.75, w: 4.8, h: 1.3, fontSize: 16, color: "DCE3F7", paraSpaceAfter: 4 });
  const items = [
    ["Q", "Capacity", "every truck carries at most Q units"],
    ["[e, l]", "Time window", "service starts inside it; waiting is allowed"],
    ["ρ(h)", "Traffic", "a trip leaving at hour h takes ρ(h) times its free flow time"],
    ["z", "Objective", "total time from leaving the depot to coming back, all trucks"],
  ];
  items.forEach(([sym, head, body], i) => {
    const y = 1.6 + i * 1.25;
    card(s, 6.6, y, 6.1, 1.05);
    T(s, sym, { x: 6.8, y: y + 0.18, w: 1.3, h: 0.7, fontFace: "Cambria", fontSize: 28, bold: true,
      color: K.cobalt, valign: "middle" });
    T(s, head, { x: 8.2, y: y + 0.14, w: 4.3, h: 0.35, fontSize: 17, bold: true });
    T(s, body, { x: 8.2, y: y + 0.5, w: 4.3, h: 0.45, fontSize: 14, color: K.soft });
  });
  s.addNotes("Pablo. The brief asks to minimize the total route duration. Level B is capacity only, level A adds time windows. We added traffic per hour because the ADEME call is about congestion and emissions: a truck in the 8:00 peak burns more for the same kilometres.");
}

// ================================================================== 3. objective v1
pres.addSection({ title: "Model" });
{
  const s = content("Our first objective could not see the clock", "Model");
  kicker(s, "Where we started  |  October");
  card(s, MX, 1.6, 6.0, 2.3);
  T(s, "Version 1: total travel time on fixed arcs", { x: MX + 0.35, y: 1.8, w: 5.4, h: 0.4, fontSize: 16, bold: true, color: K.soft });
  if (has("eq_v1.png")) s.addImage({ path: IMG("eq_v1.png"), x: MX + 0.6, y: 2.35, w: 4.4, h: 4.4 * 0.215,
    altText: "min z = sum over arcs of c_ij x_ij" });
  T(s, "c_ij is one number per pair of places, the same at 8:00 and at 22:00.", { x: MX + 0.35, y: 3.35, w: 5.4, h: 0.45, fontSize: 14, color: K.soft });
  const why = [
    ["The hour is invisible", "With a fixed c_ij, leaving in the peak or at night gives the same z: traffic, the point of the ADEME call, had no effect."],
    ["It is only distance", "At constant speed the sum is the distance: we were solving the textbook CVRP, not the brief, which says total route duration."],
    ["Waiting was free", "A truck waiting 40 min for a window to open cost nothing, yet the driver and the truck are paid for that time."],
  ];
  why.forEach(([h, b], i) => {
    const y = 1.6 + i * 1.62;
    card(s, 7.0, y, 5.7, 1.42);
    T(s, `0${i + 1}`, { x: 7.2, y: y + 0.2, w: 0.8, h: 0.6, fontFace: "Cambria", fontSize: 28, bold: true, color: K.verm });
    T(s, h, { x: 8.0, y: y + 0.17, w: 4.5, h: 0.36, fontSize: 17, bold: true });
    T(s, b, { x: 8.0, y: y + 0.55, w: 4.5, h: 0.85, fontSize: 13.5, color: K.soft });
  });
  card(s, MX, 4.2, 6.0, 2.3, K.creamDeep);
  T(s, "What the review told us", { x: MX + 0.35, y: 4.4, w: 5.4, h: 0.4, fontSize: 16, bold: true });
  T(s, "One objective, one component, exactly what the brief asks. Every symbol defined. Traffic inside the model, not as a footnote.",
    { x: MX + 0.35, y: 4.85, w: 5.3, h: 1.5, fontSize: 15 });
  s.addNotes("Pablo. Be honest: this is what we handed at the modeling check. It was a correct CVRP, but it answered a different question. Three reasons it failed, on the right. The tutor's feedback was to keep a single component and to make the model say what the brief says.");
}

// ================================================================== 4. objective v2 + traffic
{
  const s = content("We switched to the total route duration, with a traffic matrix per hour", "Model");
  kicker(s, "Version 2  |  validated");
  card(s, MX, 1.6, 5.9, 4.95);
  T(s, "Objective, one component", { x: MX + 0.35, y: 1.78, w: 5.3, h: 0.35, fontSize: 15, bold: true, color: K.soft });
  if (has("eq_v2.png")) s.addImage({ path: IMG("eq_v2.png"), x: MX + 0.45, y: 2.2, w: 4.6, h: 4.6 * 0.205, altText: "min z = sum over trucks of return time minus departure time" });
  T(s, "back at the depot minus left the depot, added over the trucks: traffic and waiting are inside z", { x: MX + 0.35, y: 3.2, w: 5.3, h: 0.6, fontSize: 13.5, color: K.soft });
  T(s, "Traffic matrix and arrival time", { x: MX + 0.35, y: 3.95, w: 5.3, h: 0.35, fontSize: 15, bold: true, color: K.soft });
  if (has("eq_traffic.png")) s.addImage({ path: IMG("eq_traffic.png"), x: MX + 0.45, y: 4.35, w: 1.9, h: 1.9 * 0.32, altText: "c_ij^h = rho_h c_ij" });
  if (has("eq_arrival.png")) s.addImage({ path: IMG("eq_arrival.png"), x: MX + 0.45, y: 5.1, w: 5.0, h: 5.0 * 0.12, altText: "a_j = t_i + s_i + sum_h c_ij^h y_ih if truck goes from i to j" });
  T(s, "y_ih = 1 picks the hour the truck leaves i; big-M switches the line off for unused arcs", { x: MX + 0.35, y: 5.8, w: 5.3, h: 0.6, fontSize: 12.5, color: K.soft });
  s.addChart(pres.charts.BAR, [{ name: "ρ(h)", labels: S.rho.map((_, h) => `${h}`), values: S.rho }], {
    x: 6.85, y: 1.55, w: 5.9, h: 3.6, barDir: "col", barGapWidthPct: 25, chartColors: [K.cobalt],
    showTitle: true, title: "Traffic factor ρ(h) by hour of departure", showLegend: false,
    valAxisMinVal: 0, valAxisMaxVal: 2, valAxisMajorUnit: 0.5, catAxisTitle: "hour", showCatAxisTitle: true,
    catAxisTitleColor: K.soft, catAxisTitleFontSize: 11, ...chartText, catAxisLabelFontSize: 9,
  });
  stat(s, 6.95, 5.35, 2.7, "×1.80", "peak at 8:00 and 17:00", K.verm, 34);
  stat(s, 9.85, 5.35, 2.8, "247.2 min", "toy optimum: ILP = full enumeration", K.cobalt, 34);
  s.addNotes("Pablo. Read the objective: for each truck, return time minus departure time. A trip leaving i during hour h takes rho_h times its free flow time; the binary y picks the hour. The profile is our assumption (peaks 1.75 to 1.80, night 1.0); the model only reads numbers, so measured data changes no equation. Check: on the 6 customer toy the ILP gives 247.16 min, exactly the brute force enumeration, 9 min better than our hand solution.");
}

// ================================================================== 5. complexity + exact limits
{
  const s = content("The problem is NP-hard, and the exact model stops at a few customers", "Model");
  kicker(s, "Why metaheuristics");
  const chain = [["Hamiltonian\ncycle", "NP-complete (Karp 1972)"], ["TSP", "1 truck, no windows, ρ = 1"], ["Our problem", "capacity, windows, traffic"]];
  chain.forEach(([h, b], i) => {
    const x = MX + i * 2.05;
    card(s, x, 1.75, 1.75, 1.5, i === 2 ? K.navy : K.white);
    T(s, h, { x: x + 0.1, y: 1.9, w: 1.55, h: 0.8, fontFace: "Cambria", fontSize: 16, bold: true, align: "center",
      color: i === 2 ? K.white : K.navy, valign: "middle" });
    T(s, b, { x: x + 0.1, y: 2.7, w: 1.55, h: 0.5, fontSize: 11, align: "center", color: i === 2 ? "DCE3F7" : K.soft });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 1.78, y: 2.35, w: 0.24, h: 0.3, fill: { color: K.verm }, line: { color: K.verm } });
  });
  T(s, "A graph has a Hamiltonian cycle if and only if our instance with K = 1 and arc times 1/(m+1) or 2/(m+1) has a plan of duration at most 1. Built in O(m²): the decision version is NP-complete.",
    { x: MX, y: 3.55, w: 5.95, h: 1.5, fontSize: 14, color: K.soft });
  T(s, "Consequence: no polynomial exact algorithm is expected; we measure where the ILP (HiGHS, 60 s) stops.",
    { x: MX, y: 5.05, w: 5.95, h: 1.0, fontSize: 15, bold: true });
  const lim = [
    [`${S.exact.traffic_min_n} to ${S.exact.traffic_max_n}`, "customers: full model with hourly traffic, proven optimal"],
    ["100", `customers: windows, no traffic, on ${S.exact.tw_proven_100.join(" and ")} (= best known)`],
    ["< 50", "customers on mixed RC101: 6 to 13 % gap at 60 s"],
  ];
  lim.forEach(([big, lab], i) => {
    const y = 1.6 + i * 1.62;
    card(s, 7.0, y, 5.7, 1.42);
    T(s, big, { x: 7.25, y: y + 0.2, w: 1.9, h: 1.0, fontFace: "Cambria", fontSize: 38, bold: true, color: [K.verm, K.cobalt, K.ochre][i], valign: "middle" });
    T(s, lab, { x: 9.2, y: y + 0.25, w: 3.3, h: 1.0, fontSize: 14, valign: "middle" });
  });
  s.addNotes("Pablo. Reduction from Hamiltonian cycle: one truck, wide windows, no traffic, arcs of the graph cost 1/(m+1), others 2/(m+1); duration 1 is reachable only through a Hamiltonian cycle. In practice the traffic model is proven up to 7 or 8 customers, because one departure hour per stop multiplies the variables by 24 and the big-M makes the LP bound useless. Without traffic the ILP proves the 100 customer C101 and R101 optimum in about 3 s and matches the published value. That is why we need metaheuristics, and the ILP gives us a reference to check them.");
}

// ================================================================== 6. three algorithms
pres.addSection({ title: "Three metaheuristics" });
{
  const s = content("Three metaheuristics, one evaluator, one protocol", "Three metaheuristics");
  kicker(s, "What we built");
  const d = {
    tabu: ["Best of 200 sampled moves each step, even if worse", "Moved customer is tabu for ~20 iterations; aspiration on a new best", "Start: time oriented nearest neighbor", "tenure 20, 200 candidates, 15 neighbors"],
    sa: ["One random move; accept a worse one with probability e^(−Δ/T)", "Temperature cools geometrically over the time budget", "Start: randomized cheapest insertion; compiled (numba)", "T₀ factor 0.005 (0.01 in the scale study), T_f 0.005"],
    grasp: ["Randomized regret insertion, then a granular descent (6 neighborhoods)", "90 kicks per iteration: remove 10 to 20 % of customers, reinsert, keep if better", "Time windows checked in O(1) per move", "α 0.3, first improvement, 90 kicks"],
  };
  ["tabu", "sa", "grasp"].forEach((a, i) => {
    const x = MX + i * 4.1;
    card(s, x, 1.6, 3.85, 4.95);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 1.85, w: 0.42, h: 0.42, fill: { color: ALG[a].color }, line: { color: ALG[a].color } });
    T(s, ALG[a].name, { x: x + 0.85, y: 1.83, w: 2.9, h: 0.45, fontFace: "Cambria", fontSize: 20, bold: true, valign: "middle" });
    T(s, ALG[a].who, { x: x + 0.85, y: 2.3, w: 2.9, h: 0.3, fontSize: 12, color: K.soft });
    const rows = [["Step", d[a][0]], ["Guidance", d[a][1]], ["Engine", d[a][2]], ["Tuned", d[a][3]]];
    rows.forEach(([h, b], j) => {
      T(s, h.toUpperCase(), { x: x + 0.3, y: 2.8 + j * 0.92, w: 3.3, h: 0.25, fontSize: 10, bold: true, color: ALG[a].color, charSpacing: 2 });
      T(s, b, { x: x + 0.3, y: 3.05 + j * 0.92, w: 3.35, h: 0.65, fontSize: 12.5 });
    });
  });
  s.addNotes("Each author presents their own algorithm in 30 seconds. Same Instance and Solution classes, same shared evaluator for capacity and windows, same time budget. Parameters were tuned on 6 instances that are never used for the test (grid of 9 to 12 settings).");
}

// ================================================================== 7. race animation
{
  const s = content("Same 100 customers, same 20 seconds: three ways to search", "Three metaheuristics");
  kicker(s, "Watch them work");
  addGif(s, "race_rc101.gif", MX + 0.2, 1.45, 11.7, 5.2 / 13.5, "Animation of the best routes of each algorithm on RC101 at 0.3, 0.6, 1, 2, 4, 8, 14 and 20 s");
  T(s, "Each frame is the best feasible plan the solver returned after t seconds (seed 1), checked by the shared evaluator. Colors are trucks; the red square is the depot.",
    { x: MX, y: 6.15, w: 12, h: 0.5, fontSize: 13, color: K.soft, italic: true });
  s.addNotes("Let the animation run once. GRASP-ILS starts from a good construction and is close to the best known value within a second; SA starts worse and descends steadily as it cools; Tabu Search keeps more trucks. This is what the statistics on the next slide summarize.");
}

// ================================================================== 8. round 1
{
  const s = content(`Round 1: GRASP-ILS wins on the 50 Solomon test instances`, "Three metaheuristics");
  kicker(s, `${S.solomon.runs} runs per algorithm  |  20 s each  |  10 seeds`);
  s.addChart(pres.charts.BAR, ORDER.map((a) => ({ name: ALG[a].name, labels: S.solomon.classes, values: S.solomon.by_class[a] })), {
    x: MX, y: 1.5, w: 7.6, h: 4.9, barDir: "col", barGapWidthPct: 60, chartColors: ORDER.map((a) => ALG[a].color),
    showTitle: true, title: "Mean gap to the best known solution, by Solomon class (%)", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisLabelFormatCode: "0", ...chartText, dataLabelFontSize: 9,
  });
  ORDER.forEach((a, i) => {
    const y = 1.55 + i * 1.3;
    card(s, 8.6, y, 4.1, 1.12);
    T(s, pct(sol[a].mean, 2), { x: 8.8, y: y + 0.15, w: 1.9, h: 0.8, fontFace: "Cambria", fontSize: 30, bold: true, color: ALG[a].color, valign: "middle" });
    T(s, `${ALG[a].name}\nworst ${pct(sol[a].worst)}, at best known ${fmt(sol[a].at_bks)} of 500`, { x: 10.7, y: y + 0.17, w: 1.95, h: 0.85, fontSize: 11.5 });
  });
  T(s, "Friedman p = 4·10⁻¹³; every pair differs (Wilcoxon, Holm, 5 %). GRASP-ILS is chosen: feasible on every run, lowest mean gap.",
    { x: 8.6, y: 5.5, w: 4.1, h: 0.95, fontSize: 13, bold: true });
  s.addNotes("Farida. 50 test instances times 10 seeds, 20 s, one machine. GRASP-ILS 1.16 % mean gap, SA 1.70 %, Tabu 3.98 %, all differences significant. Notice: GRASP-ILS does only about 19 iterations in 20 s while SA does 42 million moves; few deep searches from good starts beat many cheap moves at this size. On RC2 SA is slightly ahead. Rule fixed before the campaign: feasible, then lowest mean gap.");
}

// ================================================================== 9. not enough
pres.addSection({ title: "Round 2" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Round 2" });
  T(s, "ROUND 2  |  REVIEW OF 10 NOVEMBER", { x: MX, y: 0.55, w: 8, h: 0.3, fontSize: 12, bold: true, color: "AEB8E6", charSpacing: 3 });
  T(s, "“100 customers on Euclidean points is not the real world. Show me the limit of each algorithm.”",
    { x: MX, y: 1.0, w: 12, h: 1.5, fontFace: "Cambria", fontSize: 30, italic: true, color: K.white });
  const asks = [
    ["10 000", "customers at least"], ["Roads", "real networks, not straight lines"], ["2 countries", "same protocol, explain the difference"],
    ["Parameters", "sensitivity of each algorithm"], ["Night", "what changes outside the peak"], ["Your opinion", "which algorithm, in which scenario"],
  ];
  asks.forEach(([h, b], i) => {
    const x = MX + (i % 3) * 4.1, y = 2.85 + Math.floor(i / 3) * 1.65;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.85, h: 1.4, fill: { color: "24357E" }, line: { color: "3A4C99" }, rectRadius: 0.08 });
    T(s, h, { x: x + 0.3, y: y + 0.2, w: 3.3, h: 0.6, fontFace: "Cambria", fontSize: 26, bold: true, color: i === 5 ? "F2A08A" : K.white });
    T(s, b, { x: x + 0.3, y: y + 0.82, w: 3.3, h: 0.45, fontSize: 14, color: "DCE3F7" });
  });
  s.addNotes("Pablo. Round 1 was not enough. Every Solomon instance has 100 customers, distances are straight lines, and the best known values exist only for distance without traffic. The professor asked for six things. The rest of the talk answers them one by one, with numbers.");
}

// ================================================================== 10. new test bed
{
  const s = content("The instance problem: we needed bigger, real, and still measurable data", "Round 2");
  kicker(s, "New test bed");
  const m = S.cities.metrics;
  const rows = [
    ["Data", "Customers", "Windows", "Reference for quality", "Why"],
    ["Solomon (round 1)", "100", "yes", "best known", "tuning and statistics"],
    ["Homberger R1", "400 · 800 · 1 000", "yes", "best known", "how quality breaks with n"],
    ["Synthetic uniform", "1 000 to 10 000", "no", "best run, radial bound", "the limit in time and memory"],
    ["Paris (France)", "999 real", "no", "best of all runs", "road network, real asymmetry"],
    ["São Paulo (Brazil)", "999 real", "no", "best of all runs", "second country, same protocol"],
  ];
  s.addTable(rows.map((r, i) => r.map((c) => ({ text: c, options: {
    bold: i === 0, color: i === 0 ? K.white : K.navy, fill: { color: i === 0 ? K.navy : (i % 2 ? K.white : "F8F5EE") },
    fontSize: 13, fontFace: "Calibri", valign: "middle" } }))), { x: MX, y: 1.55, w: 7.7, colW: [1.95, 1.45, 0.95, 1.75, 1.6], rowH: 0.52,
    border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  T(s, "Road networks: OpenStreetMap through the RRNCO dataset; travel distances and free flow times are shortest paths on the real graph.",
    { x: MX, y: 4.85, w: 7.7, h: 0.75, fontSize: 13, color: K.soft });
  card(s, 8.75, 1.55, 3.95, 4.95);
  T(s, "Two cities, measured", { x: 9.0, y: 1.75, w: 3.5, h: 0.4, fontSize: 17, bold: true });
  const mrow = (lab, a, b, y) => {
    T(s, lab, { x: 9.0, y, w: 1.7, h: 0.5, fontSize: 12.5, color: K.soft });
    T(s, a, { x: 10.6, y, w: 1.0, h: 0.5, fontSize: 15, bold: true, align: "right" });
    T(s, b, { x: 11.6, y, w: 0.95, h: 0.5, fontSize: 15, bold: true, align: "right", color: K.cobalt });
  };
  T(s, "Paris", { x: 10.6, y: 2.25, w: 1.0, h: 0.3, fontSize: 11, bold: true, align: "right" });
  T(s, "S. Paulo", { x: 11.6, y: 2.25, w: 0.95, h: 0.3, fontSize: 11, bold: true, align: "right", color: K.cobalt });
  mrow("mean speed", `${fmt(m.Paris.mean_speed_kmh)} km/h`, `${fmt(m.Sao_Paulo.mean_speed_kmh)} km/h`, 2.7);
  mrow("circuity (road / straight)", fmt(m.Paris.circuity, 2), fmt(m.Sao_Paulo.circuity, 2), 3.35);
  mrow("pairs with A→B ≠ B→A", pct(m.Paris.asymmetric_pairs_pct, 0), pct(m.Sao_Paulo.asymmetric_pairs_pct, 0), 4.0);
  mrow("area covered", `${fmt(m.Paris.area_km2, 1)} km²`, `${fmt(m.Sao_Paulo.area_km2, 1)} km²`, 4.65);
  T(s, "Same area, same number of customers: differences come from the roads.", { x: 9.0, y: 5.4, w: 3.5, h: 0.9, fontSize: 12.5, italic: true, color: K.soft });
  s.addNotes("Pablo. Why these data: Homberger keeps a best known value, so we still measure a gap while n grows. 10 000 customers has no published optimum, so we compare against the best run and the radial lower bound (each route costs at least twice its farthest customer's distance). The cities give real road networks: the matrix is asymmetric in 97 to 99 % of the pairs, and roads are 1.5 to 1.65 times longer than straight lines. We planned Lyon and Cairo; the open RRNCO dataset gave us ready road matrices for Paris and Sao Paulo, so we kept France and replaced Egypt by Brazil, another emerging megacity with a different network. Same protocol. Limit: we have the travel matrices, not the road graphs, so density, degree and one way share are not measured, and both cities use the same assumed traffic profile.");
}

// ================================================================== 11. scale chart
{
  const s = content("As n grows, every algorithm loses quality, but not at the same speed", "Round 2");
  kicker(s, "Scale  |  Homberger R1, 20 s, 3 seeds");
  const R1 = { grasp: 0.68, sa: 1.59, tabu: 3.54 }; // Solomon R1 class, 100 customers, 20 s (solomon_report)
  const labels = ["100", "400", "800", "1 000"];
  s.addChart(pres.charts.LINE, ORDER.map((a) => ({ name: ALG[a].name, labels,
    values: [R1[a], ...[400, 800, 1000].map((n) => hom(a, n, 20).gap)] })), {
    x: MX, y: 1.5, w: 7.4, h: 4.95, chartColors: ORDER.map((a) => ALG[a].color), lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9,
    showTitle: true, title: "Mean gap to best known (%) against customers, 20 s budget", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.0", valAxisMinVal: 0, catAxisTitle: "customers (100: Solomon R1 class)", showCatAxisTitle: true, catAxisTitleColor: K.soft, catAxisTitleFontSize: 11, ...chartText,
  });
  const g = (a) => hom(a, 1000, 20);
  const notes = [
    [K.cobalt, "GRASP-ILS", `${pct(g("grasp").gap)} at 1 000: it finishes a single iteration in 20 s, yet its regret construction alone beats the others.`],
    [K.verm, "Simulated Annealing", `${pct(g("sa").gap)} at 1 000: ${fmt(g("sa").iterations / 1e6)} million moves are not enough: with 6 times the budget its gap is halved (next slide).`],
    [K.ochre, "Tabu Search", `${pct(g("tabu").gap)} at 1 000: ${fmt(g("tabu").routes)} trucks against ${fmt(g("grasp").routes)} for GRASP-ILS: its gap is mostly extra trucks that its moves rarely remove.`],
  ];
  notes.forEach(([c, h, b], i) => {
    const y = 1.55 + i * 1.65;
    card(s, 8.3, y, 4.4, 1.45);
    pill(s, 8.5, y + 0.2, h, c);
    T(s, b, { x: 8.5, y: y + 0.55, w: 4.05, h: 0.85, fontSize: 12.5 });
  });
  s.addNotes("Our analysis, all at 20 s. Tabu Search's limit is structural: its nearest neighbor start opens about 60 % more trucks than GRASP-ILS at 1 000 customers, and relocate and swap moves rarely empty a whole route, so the gap is mostly extra trucks. SA's limit is the time: 6 times the budget halves its gap. GRASP-ILS's limit is the time per iteration: one construction plus descent takes the whole budget at 800 customers and more, so its multi-start never starts.");
}

// ================================================================== 12. convergence gif + budget
{
  const s = content("More time helps SA most; GRASP-ILS stays ahead at every budget", "Round 2");
  kicker(s, "1 000 customers  |  20, 60, 120 s");
  addGif(s, "convergence_r1_10_1.gif", MX, 1.45, 7.6, 5.2 / 11, "Animation of the best gap against time for the three algorithms on 1 000 customers");
  const tbl = [["Gap at 1 000", "20 s", "60 s", "120 s"]].concat(ORDER.map((a) => [ALG[a].name, ...[20, 60, 120].map((t) => pct(hom(a, 1000, t).gap))]));
  s.addTable(tbl.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, fontSize: 13, fontFace: "Calibri",
    color: i === 0 ? K.white : (j === 0 ? ALG[ORDER[i - 1]].color : K.navy), fill: { color: i === 0 ? K.navy : K.white }, align: j ? "right" : "left", valign: "middle" } }))),
  { x: 8.55, y: 1.55, w: 4.15, colW: [1.75, 0.8, 0.8, 0.8], rowH: 0.45, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  const sa20 = hom("sa", 1000, 20).gap, sa120 = hom("sa", 1000, 120).gap;
  stat(s, 8.6, 3.65, 4.1, `÷${(sa20 / sa120).toFixed(1)}`, "SA gap from 20 s to 120 s at 1 000 customers: it was starved of time, not of ideas", K.verm, 38);
  T(s, `Within the 7 % target: GRASP-ILS up to 800 customers with 120 s (${pct(hom("grasp", 800, 120).gap)}); at 1 000 it needs more than 120 s (${pct(hom("grasp", 1000, 120).gap)}).`,
    { x: 8.6, y: 5.25, w: 4.1, h: 1.2, fontSize: 13, bold: true });
  s.addNotes("The animation is one 60 s run per algorithm on 1 000 customers. Read the steps: GRASP-ILS improves in rare large jumps (one iteration, then kicks), SA slides down continuously, Tabu flattens early. The table is the mean of 3 seeds. Time is a parameter of the method: with 6 times more time SA halves its gap; Tabu barely moves because its problem is the number of trucks.");
}

// ================================================================== 13. 10 000 customers
{
  const s = content("From 1 000 to 10 000 customers: who still answers?", "Round 2");
  kicker(s, "The limit  |  uniform, no windows  |  one run per size");
  const sw = S.sweep || [];
  const sizes = [...new Set(sw.map((r) => r.n))].sort((a, b) => a - b);
  const at = (a, n) => sw.find((r) => r.algorithm === a && r.n === n);
  const feas = ORDER.filter((a) => sizes.every((n) => at(a, n) && at(a, n).feasible));
  const part = ORDER.filter((a) => !feas.includes(a));
  const series = ORDER.map((a) => ({ name: ALG[a].name, labels: sizes.map((n) => fmt(n)),
    values: sizes.map((n) => (at(a, n) && at(a, n).feasible ? at(a, n).vs_bound : null)) }));
  s.addChart(pres.charts.LINE, series, {
    x: MX, y: 1.5, w: 6.9, h: 4.9, chartColors: ORDER.map((a) => ALG[a].color), lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9,
    showTitle: true, title: "Above the radial lower bound (%), against customers", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0", valAxisMinVal: 0, displayBlanksAs: "gap", ...chartText,
  });
  const g = (n) => at("grasp", n), t = (n) => at("tabu", n), sa = (n) => at("sa", n);
  const big = sizes[sizes.length - 1];
  const rows = [
    ["grasp", g(big) && !g(big).feasible ? "no plan at 10 000" : "",
      `Budget 60 s. One iteration takes it all: ${fmt(g(2000).seconds)} s at 2\u00a0000, ${fmt(g(5000).seconds)} s at 5\u00a0000, more than 684 s at 10\u00a0000 (budget 300 s).`],
    ["tabu", `${pct(t(big).vs_bound)} at 10 000`,
      `Time per iteration barely grows: ${t(1000).ms_per_iteration.toFixed(1)} ms at 1\u00a0000, ${t(big).ms_per_iteration.toFixed(1)} ms at 10\u00a0000, thanks to its neighbor lists.`],
    ["sa", `${pct(sa(big).vs_bound, 0)} at 10 000`,
      `Moves per second fall with n (${fmt(sa(1000).iterations / 60 / 1e6, 1)} million/s at 1\u00a0000, ${fmt(sa(5000).iterations / 60 / 1e6, 2)} at 5\u00a0000) and its cooling ends too early.`],
  ];
  rows.forEach(([a, head, body], i) => {
    const y = 1.55 + i * 1.65;
    card(s, 7.8, y, 4.9, 1.45);
    pill(s, 8.0, y + 0.2, `${ALG[a].name}${head ? ":  " + head : ""}`, ALG[a].color);
    T(s, body, { x: 8.0, y: y + 0.58, w: 4.5, h: 0.85, fontSize: 12.5, color: K.soft });
  });
  s.addNotes(`Pablo. Bound: a route costs at least twice its farthest customer's distance, and its load is at most Q, so the plan costs at least 2 sum d0i qi / Q. Read the chart left to right: at 1 000 customers without windows GRASP-ILS and Tabu Search are equal (46 %); from 2 000 on Tabu Search pulls ahead and the gap to the bound closes as n grows. GRASP-ILS finishes one iteration only: 60 s at 2 000, 125 s at 5 000, and at 10 000 it ran 684 s on a 300 s budget without finishing, so we stopped it. That overrun is a defect of our code: it reads the clock only between iterations. SA needs time in proportion to n. 10 000 by 10 000 matrix: 800 MB per run, so these runs were made one at a time on an 8 GB laptop; one seed each, orders of magnitude.`);
}

// ================================================================== 14. real cities
{
  const s = content("On real roads without windows, Tabu Search wins: the opposite of Solomon", "Round 2");
  kicker(s, "Paris and São Paulo  |  999 customers  |  distance  |  60 s, 5 seeds");
  const cities = ["Paris", "Sao_Paulo"];
  s.addChart(pres.charts.BAR, ORDER.map((a) => ({ name: ALG[a].name, labels: ["Paris", "São Paulo"], values: cities.map((c) => city(c, "distance", a).mean) })), {
    x: MX, y: 1.5, w: 6.9, h: 4.95, barDir: "col", barGapWidthPct: 60, chartColors: ORDER.map((a) => ALG[a].color),
    showTitle: true, title: "Total distance (km), mean of 5 seeds", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", valAxisMinVal: 0, ...chartText,
  });
  const ctl = (c, a, t, k) => S.cities.control.find((r) => r.city === c && r.algorithm === a && r.time_limit === t && (k === undefined || r.kicks === k));
  const why = [
    ["No windows, so construction matters less", "Capacity alone: every truck can take any customer. What counts is how many improving moves are made: Tabu makes about 30 000 iterations in 60 s, GRASP-ILS one."],
    ["GRASP-ILS never reaches its kicks", `With 0, 10 or 30 kicks the result is identical (${fmt(ctl("Paris", "grasp", 60, 0).mean, 1)} km in Paris): the first descent fills the 60 s.`],
    ["Five times the time does not change the order", `300 s: Tabu ${fmt(ctl("Paris", "tabu", 300).mean, 0)} km, GRASP-ILS ${fmt(ctl("Paris", "grasp", 300, 90).mean, 0)} km in Paris. Tabu at 60 s is ${pct(100 * (city("Paris", "distance", "tabu").mean / ctl("Paris", "tabu", 300).mean - 1))} above its own 300 s plan.`],
  ];
  why.forEach(([h, b], i) => {
    const y = 1.55 + i * 1.65;
    card(s, 7.8, y, 4.9, 1.45);
    T(s, h, { x: 8.05, y: y + 0.15, w: 4.45, h: 0.35, fontSize: 15, bold: true });
    T(s, b, { x: 8.05, y: y + 0.52, w: 4.45, h: 0.9, fontSize: 12.5, color: K.soft });
  });
  s.addNotes("Our analysis. Same order in both countries: Tabu, then GRASP-ILS, then SA; Paris to Sao Paulo changes the level (Sao Paulo trips are longer and more circuitous: circuity 1.65 against 1.51) but not the ranking. The control experiment answers 'is GRASP limited by the budget or by the size?': by the size, because one descent on 1 000 customers in pure Python takes the whole minute. All routes use the minimum number of trucks (57), so here quality is pure routing.");
}

// ================================================================== 15. night
{
  const p = night("Paris"), sp = night("Sao_Paulo");
  const s = content(`At night the same deliveries take ${fmt(p.cut, 1)} % less time: that is the traffic factor`, "Round 2");
  kicker(s, "The night  |  leave at 08:00 or 22:00  |  Tabu Search");
  addGif(s, "paris_day_night.gif", MX, 1.4, 8.4, 6.2 / 13.5, "Animation of trucks in Paris leaving at 08:00 and at 22:00, with a clock and the number of trucks back");
  T(s, "Straight segments join consecutive stops; travel times are road network times times ρ(h).", { x: MX, y: 5.35, w: 8.4, h: 0.35, fontSize: 11.5, italic: true, color: K.soft });
  [["Paris", p], ["São Paulo", sp]].forEach(([c, v], i) => {
    const y = 1.55 + i * 2.0;
    card(s, 9.3, y, 3.4, 1.8);
    T(s, c, { x: 9.5, y: y + 0.15, w: 3.0, h: 0.35, fontSize: 15, bold: true });
    T(s, `−${fmt(v.cut, 1)} %`, { x: 9.5, y: y + 0.5, w: 3.0, h: 0.7, fontFace: "Cambria", fontSize: 36, bold: true, color: K.cobalt });
    T(s, `${fmt(v.day)} min at 08:00 → ${fmt(v.night)} min at 22:00`, { x: 9.5, y: y + 1.2, w: 3.0, h: 0.5, fontSize: 12.5, color: K.soft });
  });
  T(s, "1 − 1/ρ(8) = 1 − 1/1.80 = 44.4 %. Routes last 32 min on average: only 1 of 57 changes hour, none crosses midnight. The night measures the size of the traffic effect; a test where the order of visits must change needs routes spanning several hours.",
    { x: MX, y: 5.75, w: 12.1, h: 0.8, fontSize: 13.5, bold: true });
  s.addNotes("Night, answered with numbers: same customers, same algorithm, the fleet leaves at 22:00 instead of 08:00. Routes that cross midnight are handled because the traffic profile repeats every 24 h. Say it before they do: the saving is the traffic factor of 8:00 (1.80), because the routes are short and stay inside one hour. The algorithms do not plan differently at night; they rank the same. Caveat: our profile is assumed, not measured, and night deliveries have other costs (noise, staff), which the model does not price.");
}

// ================================================================== 16. sensitivity
{
  const s = content("Each algorithm has one parameter that can break it", "Round 2");
  kicker(s, "Sensitivity  |  one factor at a time  |  3 seeds, 20 s");
  const panels = [["tabu", "candidates", "Tabu Search: candidate list size"], ["grasp", "perturb_kicks", "GRASP-ILS: kicks per iteration"], ["sa", "initial_temperature_factor", "SA: initial temperature factor"]];
  panels.forEach(([a, p, title], i) => {
    const x = MX + i * 4.1;
    const cur = (S.sensitivity[a] || []).filter((r) => r.parameter === p);
    if (!cur.length) { card(s, x, 1.55, 3.85, 3.9); T(s, `${title}\n(not run)`, { x: x + 0.3, y: 2.0, w: 3.3, h: 1, fontSize: 14 }); return; }
    s.addChart(pres.charts.LINE, [{ name: title, labels: cur.map((r) => `${r.value}`), values: cur.map((r) => r.mean_gap) }], {
      x, y: 1.5, w: 3.85, h: 3.9, chartColors: [ALG[a].color], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 8, showLegend: false,
      showTitle: true, title, showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.0", valAxisMinVal: 0, ...chartText, titleFontSize: 12, dataLabelFontSize: 9, catAxisLabelFontSize: 10,
    });
  });
  const sv = (a, p, v) => (S.sensitivity[a] || []).find((r) => r.parameter === p && r.value === v);
  if (sv("tabu", "candidates", 25) && sv("grasp", "perturb_kicks", 0) && sv("sa", "initial_temperature_factor", 0.0005)) {
    T(s, `Tabu Search is the most fragile: 25 candidates ${pct(sv("tabu", "candidates", 25).mean_gap)}, 800 ${pct(sv("tabu", "candidates", 800).mean_gap)}, tuned 200 ${pct(sv("tabu", "candidates", 200).mean_gap)}. GRASP-ILS without kicks doubles its gap (${pct(sv("grasp", "perturb_kicks", 0).mean_gap)} against ${pct(sv("grasp", "perturb_kicks", 90).mean_gap)}). SA is flat from 0.001 to 0.05 and breaks only near T₀ = 0 (${pct(sv("sa", "initial_temperature_factor", 0.0005).mean_gap)}): it becomes a descent.`,
      { x: MX, y: 5.55, w: 12.1, h: 0.95, fontSize: 13.5, bold: true });
  }
  s.addNotes("Mean gap on the tuning set, one parameter moved at a time around the tuned value, others fixed. Tabu: too few candidates (25) gives 20 % because the step is nearly random; too many (800) gives 8 % because each iteration is 14 times slower than with 25. GRASP-ILS: kicks are what make it better than plain GRASP; also, the tuned alpha 0.3 is not the best on these runs (alpha 0.7 to 1.0 gives 1.02 %), a more random start helps at 100 customers. SA: robust, gap between 0.54 and 0.83 % over two orders of magnitude of temperature. Every author explains their own curve.");
}

// ================================================================== 17. recommendation
pres.addSection({ title: "Recommendation" });
{
  const s = content("Our choice: GRASP-ILS for the ADEME pilot, with a rule to switch", "Recommendation");
  kicker(s, "Our own reading of our own numbers");
  const rec = [
    ["About 100 customers, time windows", "grasp", `${pct(sol.grasp.mean, 2)} mean gap, best known on ${fmt(sol.grasp.at_bks)} of 500 runs; significantly ahead of SA and Tabu Search`],
    ["One bad run is not acceptable (100 customers)", "sa", `worst run ${pct(sol.sa.worst)}, every run within 7 %; slightly ahead on wide windows (RC2)`],
    ["400 to 1 000 customers, time windows", "grasp", `lowest gap at every size and budget; within 7 % up to 800 customers with 120 s (${pct(hom("grasp", 800, 120).gap)})`],
    ["About 1 000 customers on a real road network, no windows", "tabu", `${pct(100 * (city("Paris", "distance", "tabu").mean / bestAll("Paris") - 1), 0)} to ${pct(100 * (city("Sao_Paulo", "distance", "tabu").mean / bestAll("Sao_Paulo") - 1), 0)} from the best plan found, against ${pct(100 * (city("Paris", "distance", "grasp").mean / bestAll("Paris") - 1), 0)} to ${pct(100 * (city("Sao_Paulo", "distance", "grasp").mean / bestAll("Sao_Paulo") - 1), 0)} for GRASP-ILS: 30 000 iterations against 1`],
    ["10 000 customers, no windows", "tabu", `the only good plan: ${S.synthetic.tabu ? pct(S.synthetic.tabu.vs_bound) : "n/a"} above a lower bound, minimum trucks; GRASP-ILS returns nothing`],
    ["Peak or night departure", "tabu", `as without traffic: the ranking does not change with the hour; the ${fmt(night("Paris").cut, 1)} % night saving is the traffic factor`],
  ];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 1.4, w: 12.1, h: 0.85, fill: { color: K.navy }, line: { color: K.navy }, rectRadius: 0.08 });
  T(s, [
    { text: "Final choice  ", options: { bold: true, color: "AEB8E6", fontSize: 13, charSpacing: 2 } },
    { text: "GRASP-ILS", options: { bold: true, color: K.white, fontSize: 20, fontFace: "Cambria" } },
    { text: "   the brief is the CVRPTW: time windows, a depot, a few hundred deliveries. Switch to Tabu Search above 2 000 customers or without windows.", options: { color: "DCE3F7", fontSize: 14 } },
  ], { x: MX + 0.3, y: 1.5, w: 11.5, h: 0.65, valign: "middle" });
  const rows = [["Scenario", "Choose", "Because (our data)"]].concat(rec.map((r) => [r[0], ALG[r[1]].name, r[2]]));
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { fontSize: 12, fontFace: "Calibri", valign: "middle",
    bold: i === 0 || j === 1, color: i === 0 ? K.white : (j === 1 ? ALG[rec[i - 1][1]].color : K.navy),
    fill: { color: i === 0 ? K.navy : (i % 2 ? K.white : "F8F5EE") } } }))),
  { x: MX, y: 2.45, w: 12.1, colW: [3.6, 2.1, 6.4], rowH: 0.52, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  T(s, "Caveat: windows were tested up to 1 000 customers, no windows from 1 000 to 10 000; we did not test 10 000 customers with windows.", { x: MX, y: 6.35, w: 12.1, h: 0.4, fontSize: 12.5, italic: true, color: K.soft });
  s.addNotes("Each line is backed by a slide we showed. The rule of thumb: time windows make the construction decisive (GRASP-ILS); without windows on large real networks the number of improving moves per second decides (Tabu Search); when the budget is long and the code compiled, SA catches up.");
}

// ================================================================== 18. limits
{
  const s = content("What we did not solve, and what we would do next", "Recommendation");
  kicker(s, "Transparency");
  const lim = [
    ["Equal time is not equal code", "SA is compiled (numba); Tabu Search and GRASP-ILS are pure Python. Compiling the GRASP-ILS descent is the first step to scale it."],
    ["Traffic is assumed", "ρ(h) is our profile, not measured data; with measured speeds no equation changes, only the matrix."],
    ["France against Brazil, not Egypt", "Open road matrices existed for Paris and São Paulo; Cairo needs an OSM extraction we did not validate in time."],
    ["One departure time per fleet", "The model lets each truck choose its departure; the metaheuristics fix one. A 1-D search per route would close the gap."],
    ["First in, first out", "A later departure can arrive earlier when the hour changes; cutting trips at the hour removes it."],
    ["Our solver overran its budget", "GRASP-ILS reads its clock only between iterations: 684 s on a 300 s budget at 10 000. A defect of our code, fixed by checking time inside the construction."],
  ];
  lim.forEach(([h, b], i) => {
    const x = MX + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 1.65;
    card(s, x, y, 5.95, 1.45);
    T(s, h, { x: x + 0.3, y: y + 0.17, w: 5.4, h: 0.36, fontSize: 15.5, bold: true });
    T(s, b, { x: x + 0.3, y: y + 0.56, w: 5.4, h: 0.85, fontSize: 12.5, color: K.soft });
  });
  s.addNotes("Say these before the jury asks them.");
}

// ================================================================== 19. close
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Recommendation" });
  T(s, "IN ONE SLIDE", { x: MX, y: 0.6, w: 6, h: 0.3, fontSize: 12, bold: true, color: "AEB8E6", charSpacing: 3 });
  T(s, "Our choice is GRASP-ILS for the ADEME pilot. When the city grows past 2 000 customers or has no windows, Tabu Search takes over",
    { x: MX, y: 1.0, w: 12, h: 1.5, fontFace: "Cambria", fontSize: 30, bold: true, color: K.white });
  const big = [
    [pct(sol.grasp.mean, 2), "GRASP-ILS mean gap on 500 Solomon runs, chosen method"],
    [pct(hom("grasp", 1000, 120).gap), "GRASP-ILS at 1 000 customers with time windows, 120 s"],
    [pct(S.synthetic.tabu.vs_bound), "Tabu Search above a lower bound at 10 000 customers, the only method that scales"],
  ];
  big.forEach(([b, l], i) => {
    const x = MX + i * 4.1;
    T(s, b, { x, y: 3.0, w: 3.9, h: 1.0, fontFace: "Cambria", fontSize: 48, bold: true, color: i === 2 ? "F2A08A" : K.white });
    T(s, l, { x, y: 4.05, w: 3.7, h: 0.9, fontSize: 15, color: "DCE3F7" });
  });
  T(s, "Thank you. Questions?", { x: MX, y: 5.6, w: 8, h: 0.6, fontFace: "Cambria", fontSize: 26, italic: true, color: K.white });
  s.addNotes("Close in 20 seconds: one model with traffic inside the objective, three algorithms measured to their limit, one final choice (GRASP-ILS, because the brief is the CVRPTW and it wins every windowed test up to 1 000 customers) and one rule to switch (Tabu Search beyond 2 000 customers or without windows, from the sweep and the cities). Then open questions. The Q and A preparation is in presentation/qa.md.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  const skill = process.env.PPTX_SKILL;
  if (skill) {
    const { applyTheme } = require(path.join(skill, "scripts", "apply_theme.js"));
    await applyTheme(OUT, THEME);
  }
  console.log("wrote", OUT);
})();
