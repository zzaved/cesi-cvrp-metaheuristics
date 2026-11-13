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
const OUT = path.join(HERE, process.env.STATIC ? "cvrp_final_presentation_static.pptx" : "cvrp_final_presentation.pptx");

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
  const still = process.env.STATIC && has(file.replace(".gif", ".png")) ? file.replace(".gif", ".png") : file;
  slide.addImage({ path: IMG(still), x, y, w, h: w * ratio, altText: alt });
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

// ------------------------------------------------------------------ extra helpers
// setting tags under the title: dataset, size, windows, objective, budget, reference
const tags = (slide, list, y = 1.3, dark = false) => {
  let x = MX;
  list.forEach((t) => {
    const w = 0.075 * t.length + 0.34;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.3, rectRadius: 0.06,
      fill: { color: dark ? "24357E" : K.creamDeep }, line: { color: dark ? "3A4C99" : "D9D1BD" } });
    T(slide, t, { x, y: y + 0.03, w, h: 0.24, fontSize: 10.5, bold: true, align: "center",
      color: dark ? "DCE3F7" : K.navy, valign: "middle" });
    x += w + 0.1;
  });
};
// straight segment between two points
const seg = (slide, x1, y1, x2, y2, color, width = 2.25, dash) => {
  const [ax, ay, bx, by] = x1 <= x2 ? [x1, y1, x2, y2] : [x2, y2, x1, y1];
  slide.addShape(pres.shapes.LINE, { x: ax, y: Math.min(ay, by), w: Math.max(bx - ax, 0.001),
    h: Math.max(Math.abs(by - ay), 0.001), flipV: by < ay, line: { color, width, dashType: dash || "solid" } });
};
const numDot = (slide, x, y, n, color, d = 0.34) => {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color } });
  T(slide, `${n}`, { x, y: y + 0.01, w: d, h: d, fontSize: 11, bold: true, color: K.white, align: "center", valign: "middle" });
};
const cap = (slide, text, o) => T(slide, text, { fontSize: 12, color: K.soft, italic: true, ...o });

// ================================================================== 1. title
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
  T(s, "CESI  |  ALGORITHMS AND COMBINATORIAL OPTIMIZATION  |  ADEME CALL", { x: MX, y: 0.55, w: 11, h: 0.3,
    fontSize: 12, bold: true, color: "AEB8E6", charSpacing: 2 });
  T(s, "Routing deliveries when the clock matters", { x: MX, y: 1.0, w: 6.0, h: 1.6, fontFace: "Cambria",
    fontSize: 40, bold: true, color: K.white });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 2.85, w: 5.9, h: 1.85, fill: { color: "24357E" },
    line: { color: "F2A08A", width: 1.5 }, rectRadius: 0.08 });
  T(s, "THE QUESTION", { x: MX + 0.3, y: 3.0, w: 5, h: 0.25, fontSize: 10.5, bold: true, color: "F2A08A", charSpacing: 3 });
  T(s, "Which truck serves each customer, in which order, and when does it travel, so that the total route duration is minimal?",
    { x: MX + 0.3, y: 3.3, w: 5.35, h: 1.3, fontFace: "Cambria", fontSize: 19, italic: true, color: K.white });
  T(s, "Not a shortest path between two points: we decide the assignment, the order and the timing for a whole fleet, under capacity, time windows and traffic.",
    { x: MX, y: 4.9, w: 5.9, h: 0.9, fontSize: 14, color: "DCE3F7" });
  T(s, "Pablo  ·  Dag  ·  Farida      13 November 2026", { x: MX, y: 6.15, w: 6, h: 0.35, fontSize: 14, color: K.white });

  // the problem in one picture: depot, customers (demand, window), three trucks, traffic
  const P = { d: [9.75, 3.9], c1: [7.6, 2.35], c2: [8.9, 1.55], c3: [10.35, 1.95], c4: [12.0, 2.85],
    c5: [12.35, 4.55], c6: [11.0, 5.55], c7: [8.6, 5.75], c8: [7.25, 4.35] };
  const routes = [[K.paleBlue, ["d", "c1", "c2", "c3", "d"]], ["F2A08A", ["d", "c4", "c5", "c6", "d"]], ["E9C46A", ["d", "c7", "c8", "d"]]];
  routes.forEach(([col, r]) => r.slice(1).forEach((k, i) => seg(s, ...P[r[i]], ...P[k], col, 2.5)));
  const cust = { c1: [3, "8:00-9:00"], c2: [5, ""], c3: [2, "9:00-11:00"], c4: [4, ""], c5: [5, "14:00-16:00"],
    c6: [1, ""], c7: [3, ""], c8: [2, "10:00-12:00"] };
  Object.entries(cust).forEach(([k, [q, win]]) => {
    const [x, y] = P[k];
    s.addShape(pres.shapes.OVAL, { x: x - 0.22, y: y - 0.22, w: 0.44, h: 0.44, fill: { color: K.white }, line: { color: K.navy } });
    T(s, `${q}`, { x: x - 0.22, y: y - 0.2, w: 0.44, h: 0.4, fontSize: 12, bold: true, align: "center", valign: "middle" });
    if (win) T(s, win, { x: x - 0.75, y: y + 0.25, w: 1.5, h: 0.25, fontSize: 10.5, color: "DCE3F7", align: "center" });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: P.d[0] - 0.24, y: P.d[1] - 0.24, w: 0.48, h: 0.48, fill: { color: K.verm }, line: { color: K.white, width: 1.5 } });
  T(s, "depot", { x: P.d[0] - 0.6, y: P.d[1] + 0.28, w: 1.2, h: 0.25, fontSize: 11, bold: true, color: K.white, align: "center" });
  T(s, "number = demand q   ·   label = time window   ·   color = one truck (capacity Q = 10)",
    { x: 6.9, y: 6.2, w: 6.0, h: 0.3, fontSize: 11, color: "AEB8E6", align: "center" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.95, y: 0.6, w: 1.95, h: 0.95, fill: { color: "24357E" }, line: { color: "3A4C99" }, rectRadius: 0.06 });
  T(s, "traffic by hour", { x: 11.05, y: 0.66, w: 1.75, h: 0.22, fontSize: 10, bold: true, color: "AEB8E6" });
  T(s, "08:00  trip × 1.80\n22:00  trip × 1.00", { x: 11.05, y: 0.9, w: 1.8, h: 0.6, fontSize: 11.5, color: K.white });
  s.addNotes(`PABLO (about 1 min).
"We plan the routes of a fleet of delivery trucks. On the right: one depot, the red square; eight customers, each with a demand, the number in the circle, and some with a time window, the hours under the circle; three trucks, one per color, each carrying at most Q = 10 units."
"The question is in the box: which truck serves each customer, in which order, and when it travels, so that the total time all trucks spend on the road is minimal."
"This is not a shortest path problem: a GPS finds the best road between two points. We decide who goes where, in which order, and at what time, for the whole fleet at once."
"Traffic, top right, is why the clock matters: the same trip takes 1.8 times longer at 8:00 than at night, in our model."
The picture is illustrative (made-up demands and windows), not one of our instances.`);
}

// ================================================================== 2. the problem and its variables
{
  const s = content("Three layers: capacity, then time windows, then hourly traffic", "Opening");
  kicker(s, "The problem and its notation");
  const lv = [
    ["CVRP", "Capacitated Vehicle Routing Problem", "Visit every customer once; each truck carries at most Q. Level B of the brief."],
    ["CVRPTW", "CVRP with Time Windows", "Each customer can only be served inside its window [e, l]. Level A of the brief."],
    ["+ traffic", "Our extension (ADEME call)", "A trip lasts longer or shorter depending on the hour the truck leaves."],
  ];
  lv.forEach(([h, sub, b], i) => {
    const y = 1.55 + i * 1.02;
    card(s, MX, y, 6.0, 0.9, i === 2 ? K.navy : K.white);
    T(s, h, { x: MX + 0.2, y: y + 0.12, w: 1.45, h: 0.65, fontFace: "Cambria", fontSize: 19, bold: true, color: i === 2 ? "F2A08A" : K.cobalt, valign: "middle" });
    T(s, sub, { x: MX + 1.7, y: y + 0.1, w: 4.2, h: 0.3, fontSize: 12.5, bold: true, color: i === 2 ? K.white : K.navy });
    T(s, b, { x: MX + 1.7, y: y + 0.4, w: 4.2, h: 0.45, fontSize: 11.5, color: i === 2 ? "DCE3F7" : K.soft });
  });
  // time window example
  card(s, MX, 4.7, 6.0, 2.15);
  T(s, "A time window, worked example: customer open from 09:00 to 11:00", { x: MX + 0.2, y: 4.8, w: 5.6, h: 0.3, fontSize: 12.5, bold: true });
  const x0 = MX + 0.45, x1 = MX + 5.55, hx = (h) => x0 + ((h - 8) / 4) * (x1 - x0);
  s.addShape(pres.shapes.RECTANGLE, { x: hx(9), y: 5.45, w: hx(11) - hx(9), h: 0.32, fill: { color: K.paleBlue }, line: { color: K.cobalt } });
  T(s, "window [e, l] = [09:00, 11:00]", { x: hx(9), y: 5.48, w: hx(11) - hx(9), h: 0.26, fontSize: 10.5, bold: true, color: K.cobalt, align: "center" });
  seg(s, x0, 5.95, x1, 5.95, K.soft, 1.25);
  [8, 9, 10, 11, 12].forEach((h) => T(s, `${String(h).padStart(2, "0")}:00`, { x: hx(h) - 0.3, y: 6.0, w: 0.6, h: 0.22, fontSize: 9.5, color: K.soft, align: "center" }));
  // early arrival
  s.addShape(pres.shapes.OVAL, { x: hx(8.33) - 0.08, y: 5.87, w: 0.16, h: 0.16, fill: { color: K.ochre }, line: { color: K.ochre } });
  seg(s, hx(8.33), 5.6, hx(9), 5.6, K.ochre, 2, "dash");
  T(s, "arrives 08:20: waits 40 min, starts at 09:00 (allowed)", { x: MX + 0.2, y: 6.25, w: 3.3, h: 0.5, fontSize: 10.5, color: K.ochre, bold: true });
  s.addShape(pres.shapes.OVAL, { x: hx(11.25) - 0.08, y: 5.87, w: 0.16, h: 0.16, fill: { color: K.verm }, line: { color: K.verm } });
  T(s, "arrives 11:15: after l, plan infeasible", { x: MX + 3.65, y: 6.25, w: 2.3, h: 0.5, fontSize: 10.5, color: K.verm, bold: true });
  // notation
  const items = [
    ["Q", "Capacity of a truck", "a truck carries at most Q units; a customer i asks q_i ≤ Q"],
    ["[e_i, l_i]", "Time window of customer i", "earliest and latest start of service; early: wait, late: forbidden"],
    ["ρ(h)", "Traffic factor of hour h", "a trip leaving at hour h takes ρ(h) × its free-flow time"],
    ["z", "Objective: total route duration", "sum over trucks of (return time − departure time): driving, waiting and service"],
  ];
  items.forEach(([sym, head, body], i) => {
    const y = 1.55 + i * 1.0;
    card(s, 6.85, y, 5.85, 0.88);
    T(s, sym, { x: 7.0, y: y + 0.12, w: 1.45, h: 0.62, fontFace: "Cambria", fontSize: 21, bold: true, color: K.cobalt, valign: "middle" });
    T(s, head, { x: 8.5, y: y + 0.1, w: 4.1, h: 0.3, fontSize: 13.5, bold: true });
    T(s, body, { x: 8.5, y: y + 0.42, w: 4.1, h: 0.42, fontSize: 11.5, color: K.soft });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 5.6, w: 5.85, h: 1.25, fill: { color: K.navy }, line: { color: K.navy }, rectRadius: 0.08 });
  T(s, [
    { text: "Two different ideas\n", options: { bold: true, color: "F2A08A", fontSize: 12.5 } },
    { text: "Time window: WHEN a customer can be served.\n", options: { color: K.white, fontSize: 13 } },
    { text: "Traffic: HOW LONG a trip takes, depending on WHEN it leaves.", options: { color: K.white, fontSize: 13 } },
  ], { x: 7.1, y: 5.7, w: 5.4, h: 1.1 });
  s.addNotes(`PABLO (about 1.5 min).
Left, three layers. "CVRP: every customer visited once, every truck carries at most Q. That is level B of the brief. CVRPTW adds time windows: level A. On top we add hourly traffic, because the ADEME call is about congestion."
Bottom left, the window example: "This customer accepts deliveries from 9 to 11. A truck arriving at 8:20 waits 40 minutes; that is allowed, but the waiting counts in the duration. A truck arriving at 11:15 is too late: the plan is infeasible."
Right, the notation: Q capacity; [e_i, l_i] earliest and latest start of service at customer i; rho(h) traffic multiplier of the hour h when a trip starts; z the objective, the total duration of all routes, from leaving the depot to coming back.
The navy box is the key distinction: a window says WHEN a customer can be served; traffic says HOW LONG a trip takes, depending on when it leaves. Two independent things.`);
}

// ================================================================== 3. objective v1 -> v2
pres.addSection({ title: "Model" });
{
  const s = content("Our first objective could not see the clock", "Model");
  kicker(s, "Where we started  |  October");
  card(s, MX, 1.55, 6.0, 2.75);
  T(s, "Version 1: sum of fixed arc times", { x: MX + 0.3, y: 1.65, w: 5.4, h: 0.35, fontSize: 15, bold: true, color: K.soft });
  if (has("eq_v1.png")) s.addImage({ path: IMG("eq_v1.png"), x: MX + 0.5, y: 2.02, w: 3.1, h: 3.1 * 0.215, altText: "min z = sum over arcs of c_ij x_ij" });
  T(s, "x_ij = 1 if a truck drives from i to j; c_ij = one fixed number per pair of places.", { x: MX + 0.3, y: 2.72, w: 5.5, h: 0.3, fontSize: 12, color: K.soft });
  const ex = [["Trip A → B, free-flow 10 min", "leave 08:00", "leave 22:00"], ["Version 1 counts", "10 min", "10 min"], ["With hourly traffic", "18 min", "10 min"]];
  s.addTable(ex.map((r, i) => r.map((c, j) => ({ text: c, options: { fontSize: 11.5, fontFace: "Calibri", bold: i === 0 || j === 0,
    color: i === 0 ? K.white : (i === 2 && j === 1 ? K.verm : K.navy), fill: { color: i === 0 ? K.navy : K.white }, align: j ? "center" : "left", valign: "middle" } }))),
  { x: MX + 0.3, y: 3.1, w: 5.4, colW: [2.6, 1.4, 1.4], rowH: 0.34, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  const why = [
    ["The hour is invisible", "With a fixed c_ij, the 08:00 peak and 22:00 give the same z: traffic, the point of the ADEME call, had no effect.", "each trip is priced at the hour it starts (next slide)"],
    ["It was only distance", "At constant speed the sum of arc times is the distance: the textbook CVRP, not the brief, which asks for the total route duration.", "the target is time on the road, not km"],
    ["Waiting was free", "A truck arriving at 08:20 at a customer who opens at 09:00 waits 40 min. The driver is paid, yet Version 1 counted 0.", "the 40 min push the return time later, so they are in z"],
  ];
  why.forEach(([h, b, fix], i) => {
    const y = 1.55 + i * 1.79;
    card(s, 7.0, y, 5.7, 1.65);
    T(s, `0${i + 1}`, { x: 7.15, y: y + 0.15, w: 0.7, h: 0.6, fontFace: "Cambria", fontSize: 26, bold: true, color: K.verm });
    T(s, h, { x: 7.9, y: y + 0.1, w: 4.65, h: 0.32, fontSize: 15, bold: true });
    T(s, b, { x: 7.9, y: y + 0.44, w: 4.65, h: 0.7, fontSize: 12, color: K.soft });
    T(s, [{ text: "Version 2: ", options: { bold: true, color: K.cobalt } }, { text: fix }], { x: 7.9, y: y + 1.17, w: 4.65, h: 0.4, fontSize: 12 });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 4.45, w: 6.0, h: 2.4, fill: { color: K.navy }, line: { color: K.navy }, rectRadius: 0.08 });
  T(s, "VERSION 2  |  VALIDATED", { x: MX + 0.3, y: 4.57, w: 5, h: 0.25, fontSize: 10.5, bold: true, color: "F2A08A", charSpacing: 3 });
  if (has("eq_v2_white.png")) s.addImage({ path: IMG("eq_v2_white.png"), x: MX + 0.3, y: 4.9, w: 3.6, h: 3.6 * 0.214, altText: "min z = sum over trucks of return time minus departure time" });
  T(s, "For each truck k: time back at the depot (t_{n+1}^k) minus time it left (t_0^k), added over the trucks. One component, exactly the brief's \"total route duration\": driving, waiting and service are all inside it.",
    { x: MX + 0.3, y: 5.75, w: 5.45, h: 1.05, fontSize: 12, color: "DCE3F7" });
  s.addNotes(`PABLO (about 1.5 min).
"This is what we handed in at the modeling check. Version 1 minimised the sum of fixed arc times c_ij x_ij: x_ij is 1 if a truck drives from i to j."
Point to the table: "A trip from A to B that takes 10 minutes on empty roads. In Version 1 it costs 10 whether the truck leaves at 8:00 or at 22:00. In reality, with our traffic factor, it takes 18 minutes at 8:00."
Three reasons it failed, right: the hour had no effect; the sum is just distance, so we were solving the textbook CVRP; and waiting cost nothing, although a truck that arrives 40 minutes early keeps the driver paid.
Bottom: "Version 2 has one component: for every truck, return time minus departure time, added over the trucks. Traffic and waiting are inside it automatically, because they push the return time later."`);
}

// ================================================================== 4. the hourly traffic matrix
{
  const s = content("How the hourly traffic matrix is built", "Model");
  kicker(s, "The core of the model");
  const steps = [
    ["Road network", "streets of the city (OpenStreetMap)"],
    ["Shortest paths", "best road route between every pair of places"],
    ["Base matrix C = [c_ij]", "free-flow time from i to j (empty roads)"],
    ["Traffic factor ρ(h)", "one number per hour of the day (our assumption)"],
    ["Hourly matrix", "c_ij^h = ρ(h) × c_ij"],
  ];
  steps.forEach(([h, b], i) => {
    const x = MX + i * 2.45;
    card(s, x, 1.5, 2.2, 1.2, i === 4 ? K.navy : K.white);
    numDot(s, x + 0.12, 1.62, i + 1, i === 3 ? K.verm : K.cobalt, 0.3);
    T(s, h, { x: x + 0.5, y: 1.6, w: 1.65, h: 0.45, fontSize: 12.5, bold: true, color: i === 4 ? K.white : K.navy, valign: "middle" });
    T(s, b, { x: x + 0.15, y: 2.08, w: 1.95, h: 0.6, fontSize: 10.5, color: i === 4 ? "DCE3F7" : K.soft });
    if (i < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.22, y: 1.98, w: 0.2, h: 0.24, fill: { color: K.verm }, line: { color: K.verm } });
  });
  T(s, "Real road-network matrices (steps 1 to 3)  +  assumed hourly traffic profile (step 4, the same for Paris and São Paulo)",
    { x: MX, y: 2.8, w: 12.1, h: 0.3, fontSize: 12.5, bold: true, color: K.verm });
  // worked example
  card(s, MX, 3.2, 5.95, 3.65);
  T(s, "Worked example: free-flow time A → B = 10 min", { x: MX + 0.2, y: 3.3, w: 5.6, h: 0.3, fontSize: 13, bold: true });
  const ex = [["Truck leaves A at", "ρ(h)", "Trip A → B takes"], ["08:00 (peak)", "1.80", "18 min"], ["14:00", "1.20", "12 min"], ["22:00 (night)", "1.00", "10 min"]];
  s.addTable(ex.map((r, i) => r.map((c, j) => ({ text: c, options: { fontSize: 12, fontFace: "Calibri", bold: i === 0 || j === 2,
    color: i === 0 ? K.white : K.navy, fill: { color: i === 0 ? K.navy : K.white }, align: j ? "center" : "left", valign: "middle" } }))),
  { x: MX + 0.2, y: 3.68, w: 5.55, colW: [2.2, 1.35, 2.0], rowH: 0.3, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  T(s, "Each leg uses the hour the truck leaves its current stop, not the hour it left the depot: a route starting at 07:40 can drive its first leg at ρ(7) = 1.75 and a later leg at ρ(9) = 1.40.",
    { x: MX + 0.2, y: 4.95, w: 5.6, h: 0.75, fontSize: 11.5, color: K.soft });
  T(s, [
    { text: "In the exact model: ", options: { bold: true } },
    { text: "a_j = t_i + s_i + ρ(h) c_ij for the hour h with y_ih = 1. " },
    { text: "y_ih", options: { bold: true, color: K.cobalt } },
    { text: " is a yes/no variable: 1 if the truck leaves customer i during hour h. It picks which hourly matrix prices the next trip (t_i service start, s_i service time, a_j arrival)." },
  ], { x: MX + 0.2, y: 5.72, w: 5.6, h: 1.1, fontSize: 11.5 });
  // profile chart
  s.addChart(pres.charts.BAR, [{ name: "ρ(h)", labels: S.rho.map((_, h) => `${h}`), values: S.rho }], {
    x: 6.75, y: 3.15, w: 6.0, h: 2.55, barDir: "col", barGapWidthPct: 25, chartColors: [K.cobalt],
    showTitle: true, title: "Assumed traffic factor ρ(h)", showLegend: false,
    valAxisMinVal: 0, valAxisMaxVal: 2, valAxisMajorUnit: 0.5, ...chartText, catAxisLabelFontSize: 9, titleFontSize: 12,
    showCatAxisTitle: true, catAxisTitle: "hour h when the truck leaves its current stop (0 to 23)",
    showValAxisTitle: true, valAxisTitle: "× free-flow time", catAxisTitleColor: K.soft, valAxisTitleColor: K.soft,
    catAxisTitleFontSize: 10, valAxisTitleFontSize: 10,
  });
  T(s, [
    { text: "1.80 at 08:00 and 17:00: ", options: { bold: true, color: K.verm } },
    { text: "rush hours, a trip takes 80 % longer. " },
    { text: "1.00 from 22:00 to 04:59: ", options: { bold: true, color: K.cobalt } },
    { text: "empty roads, free-flow time. The values are our assumption, not measured congestion; measured speeds would change the numbers, not one equation." },
  ], { x: 6.85, y: 5.8, w: 5.85, h: 1.05, fontSize: 11.5 });
  s.addNotes(`PABLO (about 2 min). This is the most important model slide.
Read the chain left to right: "We start from a road network. Shortest paths on it give, for each pair of places, the travel time on empty roads: that is the base matrix C, with entries c_ij. Then we apply a traffic factor rho(h), one number per hour. Multiplying gives one matrix per hour: c_ij^h = rho(h) times c_ij."
Red line: "Be precise: steps 1 to 3 are real data for Paris and Sao Paulo. Step 4 is our assumption, and it is the same profile in both cities. We did not measure hourly congestion."
Worked example: "A to B takes 10 minutes on empty roads. Leaving at 8:00, rho is 1.80, so 18 minutes; at 14:00, 1.20, so 12; at 22:00, 1.00, so 10."
"The factor applies leg by leg, by the hour the truck leaves its current stop, not the hour it left the depot."
Chart: horizontal axis = hour of departure of a leg, 0 to 23; vertical axis = how many times the free-flow time the trip takes. Peaks 1.75 to 1.80 at 7-8 h and 17-18 h; 1.00 at night because roads are empty.
y_ih: "In the exact model, y_ih is a binary that says: the truck leaves customer i during hour h. It selects which hourly matrix prices the next trip."
Check we did: on a 6-customer toy, the ILP optimum (247.16 min) equals a full enumeration of all plans.`);
}

// ================================================================== 5. complexity + exact limits
{
  const s = content("The problem is NP-hard, and the exact model stops at a few customers", "Model");
  kicker(s, "Why metaheuristics");
  T(s, "NP-hard, in our words: no known algorithm solves every instance in a time that grows polynomially with n. For an exact solver, each extra customer multiplies the number of possible plans.",
    { x: MX, y: 1.45, w: 6.1, h: 0.75, fontSize: 12.5 });
  // reduction diagram
  card(s, MX, 2.3, 2.25, 1.15);
  T(s, "Hamiltonian cycle", { x: MX + 0.1, y: 2.38, w: 2.05, h: 0.4, fontSize: 14, bold: true, align: "center", fontFace: "Cambria" });
  T(s, "a cycle through every vertex once? NP-complete (Karp 1972)", { x: MX + 0.1, y: 2.78, w: 2.05, h: 0.6, fontSize: 10, align: "center", color: K.soft });
  s.addShape(pres.shapes.RIGHT_ARROW, { x: MX + 2.33, y: 2.68, w: 1.35, h: 0.38, fill: { color: K.verm }, line: { color: K.verm } });
  T(s, "built in O(m²)", { x: MX + 2.3, y: 3.1, w: 1.4, h: 0.25, fontSize: 10, align: "center", color: K.verm, bold: true });
  card(s, MX + 3.8, 2.3, 2.3, 1.15, K.navy);
  T(s, "Our problem, decision version", { x: MX + 3.9, y: 2.38, w: 2.1, h: 0.45, fontSize: 12.5, bold: true, align: "center", color: K.white });
  T(s, "is there a plan with z ≤ B?", { x: MX + 3.9, y: 2.85, w: 2.1, h: 0.5, fontSize: 11, align: "center", color: "DCE3F7" });
  card(s, MX, 3.6, 6.1, 2.15);
  T(s, "The construction, from a graph with vertices u_0 … u_m", { x: MX + 0.2, y: 3.68, w: 5.7, h: 0.3, fontSize: 12.5, bold: true });
  T(s, [
    { text: "one truck (K = 1), demand 1 each, Q = m; windows = the whole day; ρ = 1", options: { bullet: true, breakLine: true } },
    { text: "travel time 1/(m+1) on an edge of the graph, 2/(m+1) on a non-edge", options: { bullet: true, breakLine: true } },
    { text: "threshold B = 1", options: { bullet: true } },
  ], { x: MX + 0.2, y: 4.0, w: 5.75, h: 0.9, fontSize: 11.5, paraSpaceAfter: 2 });
  T(s, "A tour has m + 1 legs. Only edges: duration exactly 1. One non-edge: at least (m+2)/(m+1) > 1. So a plan with z ≤ 1 exists if and only if the graph has a Hamiltonian cycle.",
    { x: MX + 0.2, y: 4.92, w: 5.75, h: 0.8, fontSize: 11.5, bold: true, color: K.cobalt });
  T(s, "Consequence: exact methods cannot scale; we use the ILP to check small cases and as a reference, and metaheuristics for real sizes.",
    { x: MX, y: 5.9, w: 6.1, h: 0.85, fontSize: 12.5, bold: true });
  // ILP limits
  T(s, "Where our ILP stops  (HiGHS solver, 60 s per solve)", { x: 7.0, y: 1.45, w: 5.7, h: 0.3, fontSize: 13, bold: true });
  const lim = [
    [`${S.exact.traffic_min_n} to ${S.exact.traffic_max_n}`, "customers", "Full model with hourly traffic (duration): proven optimal up to 8 on C101 and R101, 7 on RC101; never at 9 or 10.", K.verm],
    ["100", "customers", `Time windows, no traffic, distance: proven optimal on ${S.exact.tw_proven_100.join(" and ")} (equal to the best known value).`, K.cobalt],
    ["25", "customers", "Same setting on the mixed RC101: proven up to 25; from 50 on, 6 to 13 % between plan and bound at 60 s.", K.ochre],
  ];
  lim.forEach(([big, unit, lab, col], i) => {
    const y = 1.85 + i * 1.32;
    card(s, 7.0, y, 5.7, 1.18);
    T(s, big, { x: 7.15, y: y + 0.12, w: 1.6, h: 0.6, fontFace: "Cambria", fontSize: 30, bold: true, color: col, valign: "middle", align: "center" });
    T(s, unit, { x: 7.15, y: y + 0.75, w: 1.6, h: 0.3, fontSize: 10.5, color: K.soft, align: "center" });
    T(s, lab, { x: 8.85, y: y + 0.12, w: 3.7, h: 0.98, fontSize: 11.5, valign: "middle" });
  });
  cap(s, "Three different settings: the sizes are not comparable with each other. Traffic is what makes the model hard (24 hourly copies of each departure, weak big-M bounds).",
    { x: 7.0, y: 5.9, w: 5.7, h: 0.85 });
  s.addNotes(`PABLO (about 1.5 min).
"NP-hard means: nobody knows an algorithm that solves every instance in polynomial time. In practice, each extra customer multiplies the number of plans, so exact solvers hit a wall."
The proof, left: "We reduce Hamiltonian cycle, a known NP-complete problem, directly to the decision version of our problem: 'is there a plan of duration at most B?'. Given a graph with m+1 vertices, we build in O(m^2) an instance: one truck, unit demands, capacity m, windows covering the whole day, rho = 1. A trip costs 1/(m+1) along an edge of the graph and 2/(m+1) along a non-edge. Threshold B = 1."
"A tour visits m+1 legs. If every leg is an edge, the duration is exactly 1. One non-edge makes it at least (m+2)/(m+1), more than 1. So a plan of duration 1 exists exactly when the graph has a Hamiltonian cycle." Both directions are proven in section 2 of the notebook. The decision version is also in NP (a plan is checked in O(n + K)).
Right: three DIFFERENT experiments, all HiGHS with 60 s: the full traffic model is proven only up to 7 to 8 customers; without traffic, with windows, C101 and R101 are proven at 100 customers; RC101 only to 25. That is why we need metaheuristics.`);
}

// ================================================================== 6. three algorithms
pres.addSection({ title: "Three metaheuristics" });
{
  const s = content("Three metaheuristics: how each one searches", "Three metaheuristics");
  kicker(s, "What we built  |  same instance, same evaluator, same time budget");
  const d = {
    tabu: {
      steps: [
        "Start: time-oriented nearest neighbor (go to the closest customer that keeps the route feasible).",
        "Sample 200 moves (relocate, swap, 2-opt, 2-opt*) near each customer's 15 closest neighbors: the full neighborhood is too large.",
        "Apply the best sampled move that is not tabu, even if it makes the plan worse: this is how it leaves a local optimum.",
        "Tabu memory: a moved customer cannot move again for 10 to 30 iterations (tenure 20), so the search does not cycle back.",
        "Aspiration: a tabu move is allowed if it gives a new best plan.",
      ],
      idea: "Memory, not chance, drives it away from where it has been.",
      intr: "tenure 20 · 200 candidates · 15 neighbors; the candidate list is the fragile one",
      extr: "windows alone hurt it (extra trucks); hourly traffic and very large n favor it",
    },
    sa: {
      steps: [
        "Start: randomized cheapest insertion (each customer at its cheapest feasible place).",
        "Draw one random move among 5: relocate one customer or a chain of 2 to 3, swap, 2-opt, 2-opt*.",
        "Δ = new cost − current cost. If Δ ≤ 0 (better or equal), accept.",
        "If Δ > 0, accept with probability e^(−Δ/T). Example: Δ = 5 accepted 61 % of the time at T = 10, 0.7 % at T = 1.",
        "T (temperature) falls from T₀ to T_f over the time budget: early it explores, at the end it only descends.",
      ],
      idea: "Chance, controlled by T, lets it accept worse plans early on.",
      intr: "T₀ = 0.005 × start cost · T_f 0.005; robust, flat from 0.001 to 0.05",
      extr: "needs time: a longer budget helps it most; large n starves it",
    },
    grasp: {
      steps: [
        "Construct (GRASP): regret insertion, serving first customers with few good options; pick at random among the best (α = 0.3).",
        "Local search: descent over 6 neighborhoods (relocate, swap, 2-opt*, Or-opt, 2-opt, cross-exchange), granular, first improvement.",
        "Perturbation (ILS, \"kick\" in our code): ruin 10 to 20 % of the customers around a random one, recreate by cheapest insertion, descend; keep only if better.",
        "Up to P = 90 perturbations per iteration, then a new construction; keep the best plan over all iterations.",
        "Time windows checked in O(1) per move (forward and backward time slack per route).",
      ],
      idea: "Good random starts, deep descents, perturbations to escape.",
      intr: "α 0.3 · P = 90 perturbations · 20 neighbors; P matters most",
      extr: "windows favor it; hourly traffic and n ≥ 5 000 make its iterations too slow",
    },
  };
  ["tabu", "sa", "grasp"].forEach((a, i) => {
    const x = MX + i * 4.1;
    card(s, x, 1.45, 3.9, 5.42);
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 1.58, w: 0.36, h: 0.36, fill: { color: ALG[a].color }, line: { color: ALG[a].color } });
    T(s, ALG[a].name, { x: x + 0.65, y: 1.55, w: 2.4, h: 0.42, fontFace: "Cambria", fontSize: 17, bold: true, valign: "middle" });
    T(s, ALG[a].who, { x: x + 2.95, y: 1.6, w: 0.8, h: 0.3, fontSize: 11, color: K.soft, align: "right" });
    d[a].steps.forEach((st, j) => {
      const y = 2.05 + j * 0.67;
      numDot(s, x + 0.18, y + 0.03, j + 1, ALG[a].color, 0.27);
      T(s, st, { x: x + 0.55, y, w: 3.25, h: 0.66, fontSize: 10 });
    });
    T(s, d[a].idea, { x: x + 0.2, y: 5.42, w: 3.55, h: 0.4, fontSize: 10.5, bold: true, italic: true, color: ALG[a].color });
    seg(s, x + 0.2, 5.86, x + 3.7, 5.86, "E3DCCB", 0.75);
    T(s, [{ text: "Intrinsic (we choose): ", options: { bold: true, color: K.navy } }, { text: d[a].intr, options: { color: K.soft } }],
      { x: x + 0.2, y: 5.92, w: 3.55, h: 0.44, fontSize: 9.5 });
    T(s, [{ text: "Extrinsic (the scenario): ", options: { bold: true, color: K.navy } }, { text: d[a].extr, options: { color: K.soft } }],
      { x: x + 0.2, y: 6.38, w: 3.55, h: 0.44, fontSize: 9.5 });
  });
  s.addNotes(`Each author explains their own column in about 40 s; anyone must be able to explain all three.
TABU (Pablo): starts from a nearest-neighbor plan. A neighborhood move changes the plan a little: relocate moves one customer, swap exchanges two, 2-opt reverses a piece of a route, 2-opt* exchanges the ends of two routes. Evaluating all moves at 1 000 customers is millions per step, so it samples 200, each near one of a customer's 15 closest neighbors. It takes the best one even if it is worse; to avoid undoing it right away, the customers it moved are tabu for 10 to 30 iterations (tenure 20, drawn at random to avoid cycles). Aspiration: a tabu move is still allowed if it beats the best plan ever found.
SA (Dag): one random move per step. Delta is the change in cost; T, the temperature, is the tolerance for getting worse. Improvements are always accepted; a worse plan is accepted with probability e^(-Delta/T). Example: Delta = 5, T = 10 gives e^-0.5 = 61 %; T = 1 gives e^-5 = 0.7 %. T falls exponentially from T0 to Tf exactly over the time budget, so the search ends as a pure descent.
GRASP-ILS (Farida): GRASP builds a plan by regret insertion (customers with few good options first) with randomness controlled by alpha (0 greedy, 1 random). Then a descent over six neighborhoods. ILS adds PERTURBATIONS. If asked "is it really called a kick?": the standard ILS term is perturbation (Lourenco, Martin and Stutzle 2003); kick is the older informal name from the double-bridge move for the TSP (Martin, Otto and Felten 1991), and our code keeps it in the parameter name perturb_kicks. Ours is a ruin and recreate move: remove 10 to 20 % of the customers (a random one, its nearest neighbors, then random ones), reinsert them tightest window first at their cheapest place, descend, and keep the result only if it is better. Up to 90 per iteration. At 1 000 customers the construction and first descent take about 2 s and the perturbations fill the rest of the budget, so there is no second construction; from 5 000 customers the construction and descent alone exceed a 60 s budget (slide 13).
Parameters were tuned on 6 instances never used in the test.
Bottom of each column: INTRINSIC = the algorithm's own parameters, which we choose (studied one at a time on slide 17). EXTRINSIC = the scenario, which the algorithm does not choose: size, time windows, road network, budget, hour (slides 8 and 11 to 15). Tabu: candidate list is the fragile parameter; windows alone hurt it (extra trucks), hourly traffic and very large n favor it. SA: robust to temperature; needs time. GRASP-ILS: the number of perturbations matters most; windows favor it, hourly traffic (exact time-dependent evaluation) and n of 5 000 or more make its iterations too slow.`);
}

// ================================================================== 7. race animation
{
  const s = content("Same 100 customers, same 20 seconds: three ways to search", "Three metaheuristics");
  kicker(s, "Watch them work");
  tags(s, ["Solomon RC101", "100 customers", "time windows", "objective: distance", "20 s", "seed 1"]);
  addGif(s, "race_rc101.gif", MX + 0.3, 1.75, 11.5, 5.2 / 13.5, "Animation of the best routes of each algorithm on RC101 at 0.3, 0.6, 1, 2, 4, 8, 14 and 20 s");
  const leg = [
    ["Red square", "the depot"], ["Dots", "the 100 customers"], ["One color", "one truck's route"],
    ["cost", "total distance of the plan"], ["gap", "% above the best known value"], ["t = …", "seconds since the start: 0.3, 0.6, 1, 2, 4, 8, 14, 20"],
  ];
  leg.forEach(([h, b], i) => {
    const x = MX + (i % 3) * 4.05, y = 6.25 + Math.floor(i / 3) * 0.3;
    T(s, [{ text: `${h}: `, options: { bold: true, color: K.navy } }, { text: b, options: { color: K.soft } }], { x, y, w: 4.0, h: 0.28, fontSize: 11.5 });
  });
  s.addNotes(`FARIDA (about 1 min). Let the animation run once.
"Same instance, RC101, 100 customers with time windows; same 20-second budget, same seed. Each panel is the best feasible plan the solver has found at time t, shown in the title: 0.3, 0.6, 1, 2, 4, 8, 14 and 20 seconds. Each colored line is one truck's route; the red square is the depot."
"Above each panel: cost is the total distance, gap is how far above the best known value from the literature, trucks is the number of routes."
"Same problem, same evaluator, same time: only the way of searching differs. GRASP-ILS starts from a strong construction and is close early; SA starts worse and goes down as it cools; Tabu improves step by step. At 20 s all three use 17 trucks: the difference is the routing (gap 1.3 %, 2.2 %, 2.8 % on this seed)."
This is one seed on one instance; the next slide is the statistics over 500 runs.`);
}

// ================================================================== 8. round 1
{
  const s = content(`Round 1: GRASP-ILS wins on the 50 Solomon test instances`, "Three metaheuristics");
  kicker(s, "The benchmark");
  tags(s, ["Solomon", "50 test instances", "100 customers", "time windows", "objective: distance", "10 seeds × 20 s", "vs best known"]);
  s.addChart(pres.charts.BAR, ORDER.map((a) => ({ name: ALG[a].name, labels: S.solomon.classes, values: S.solomon.by_class[a] })), {
    x: MX, y: 1.7, w: 7.4, h: 3.95, barDir: "col", barGapWidthPct: 60, chartColors: ORDER.map((a) => ALG[a].color),
    showTitle: true, title: "Mean gap to the best known solution, by class (%)", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisLabelFormatCode: "0", ...chartText, dataLabelFontSize: 9,
    showValAxisTitle: true, valAxisTitle: "gap (%)", valAxisTitleColor: K.soft, valAxisTitleFontSize: 10,
  });
  T(s, [
    { text: "Classes: ", options: { bold: true } },
    { text: "C clustered customers, R random, RC mixed. Suffix 1: tight windows, short day, small trucks; suffix 2: wide windows, long day, large trucks.\n" },
    { text: "Gap (%) = (our cost − best known) / best known × 100. ", options: { bold: true } },
    { text: "Best known = best published plan (distance); not a lower bound." },
  ], { x: MX, y: 5.75, w: 7.4, h: 1.1, fontSize: 11.5 });
  ORDER.forEach((a, i) => {
    const y = 1.75 + i * 1.0;
    card(s, 8.3, y, 4.4, 0.88);
    T(s, pct(sol[a].mean, 2), { x: 8.45, y: y + 0.1, w: 1.75, h: 0.68, fontFace: "Cambria", fontSize: 26, bold: true, color: ALG[a].color, valign: "middle" });
    T(s, `${ALG[a].name}\nworst run ${pct(sol[a].worst)}  ·  feasible 500 / 500`, { x: 10.2, y: y + 0.13, w: 2.45, h: 0.65, fontSize: 11 });
  });
  card(s, 8.3, 4.85, 4.4, 2.0, K.creamDeep);
  T(s, [
    { text: "Is the difference real or luck?\n", options: { bold: true, fontSize: 12.5 } },
    { text: "Friedman test (do the three differ at all?): p = 4·10⁻¹³, yes. Wilcoxon test per pair, Holm correction: every pair differs at 5 %.\n", options: { fontSize: 11 } },
    { text: "Choice rule fixed before the runs: feasible on every run, then lowest mean gap: GRASP-ILS.", options: { fontSize: 11, bold: true, color: K.cobalt } },
  ], { x: 8.5, y: 4.95, w: 4.05, h: 1.85 });
  s.addNotes(`FARIDA (about 1.5 min).
Setup: "Solomon is the standard benchmark for routing with time windows: 56 instances of 100 customers. We tuned on 6 and tested on the other 50, 10 seeds each, 20 seconds per run: 500 runs per algorithm, 1 500 in total, same machine."
"The objective here is distance, because the published best known values are distances. Same solvers; only the route cost function changes."
Classes: C clustered, R random, RC mixed; suffix 1 has tight windows and small trucks, suffix 2 wide windows and large trucks.
Gap: our cost minus the best known, divided by the best known. Reference = best known plan, not a lower bound.
Result: GRASP-ILS 1.16 %, SA 1.70 %, Tabu 3.98 %. Statistics: Friedman says the three are not equal (p = 4e-13); pairwise Wilcoxon with Holm correction says each pair differs. So the ranking is not visual noise.
Rule fixed before the campaign: every run feasible, then lowest mean gap. GRASP-ILS wins. Note SA's worst run (6.5 %) is the best of the three, and SA is close on RC2.`);
}

// ================================================================== 9. round 2 transition
pres.addSection({ title: "Round 2" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Round 2" });
  T(s, "ROUND 2  |  WHAT CHANGED AFTER THE REVIEW OF 10 NOVEMBER", { x: MX, y: 0.55, w: 11, h: 0.3, fontSize: 12, bold: true, color: "AEB8E6", charSpacing: 3 });
  T(s, "“100 customers on Euclidean points is not the real world. Show me the limit of each algorithm.”",
    { x: MX, y: 0.95, w: 12, h: 1.2, fontFace: "Cambria", fontSize: 26, italic: true, color: K.white });
  T(s, "Round 1 answered “which algorithm is best on the benchmark”. Round 2 sets six new objectives:",
    { x: MX, y: 2.2, w: 12, h: 0.4, fontSize: 15, color: "DCE3F7" });
  const asks = [
    ["Larger instances", "400 to 10 000 customers, not only 100", "slides 11 to 13"],
    ["Real road networks", "real streets in two countries, with and without windows", "slides 10, 14, 15"],
    ["Scalability", "where each algorithm breaks, and why", "slides 11 to 13"],
    ["Parameter sensitivity", "how fragile each tuned setting is", "slide 17"],
    ["Departure time", "what the hour does to route duration", "slides 15, 16"],
    ["A recommendation", "which algorithm, in which scenario", "slide 18"],
  ];
  asks.forEach(([h, b, where], i) => {
    const x = MX + (i % 3) * 4.1, y = 2.85 + Math.floor(i / 3) * 1.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.85, h: 1.55, fill: { color: "24357E" }, line: { color: "3A4C99" }, rectRadius: 0.08 });
    numDot(s, x + 0.25, y + 0.22, i + 1, i === 5 ? K.verm : K.cobalt, 0.36);
    T(s, h, { x: x + 0.75, y: y + 0.18, w: 3.0, h: 0.45, fontFace: "Cambria", fontSize: 19, bold: true, color: i === 5 ? "F2A08A" : K.white });
    T(s, b, { x: x + 0.3, y: y + 0.7, w: 3.35, h: 0.45, fontSize: 13, color: "DCE3F7" });
    T(s, where, { x: x + 0.3, y: y + 1.17, w: 3.35, h: 0.28, fontSize: 11, bold: true, color: "AEB8E6" });
  });
  s.addNotes(`FARIDA (about 45 s).
"Round 1 told us which algorithm wins on the standard benchmark. The professor's review said that is not enough: 100 customers on points joined by straight lines is not a city."
"So round 2 has six objectives: larger instances; real road networks; scalability, meaning where each method breaks and why; sensitivity of the parameters; the effect of the departure hour; and our own recommendation per scenario. Each tile says which slide answers it."`);
}

// ================================================================== 10. new test bed
{
  const s = content("A new test bed: each dataset answers one question", "Round 2");
  kicker(s, "Data");
  const m = S.cities.metrics;
  const rows = [
    ["Dataset", "Customers", "Windows", "Objective", "Reference", "What it tests"],
    ["Solomon (round 1)", "100", "yes", "distance", "best known", "quality, statistics"],
    ["Homberger R1", "400 · 800 · 1 000", "yes", "distance", "best known", "scale, windows"],
    ["Synthetic uniform", "1 000 to 10 000", "no", "distance", "lower bound", "computing limit"],
    ["Paris (France)", "999 (and 300)", "no + yes", "km, time, duration", "best of our runs", "real roads"],
    ["São Paulo (Brazil)", "999 (and 300)", "no + yes", "km, time, duration", "best of our runs", "second country"],
  ];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
    bold: i === 0 || j === 0, color: i === 0 ? K.white : (j === 2 && c === "no" ? K.verm : K.navy), fill: { color: i === 0 ? K.navy : (i % 2 ? K.white : "F8F5EE") },
    fontSize: 11, fontFace: "Calibri", valign: "middle" } }))), { x: MX, y: 1.5, w: 8.0, colW: [1.75, 1.4, 0.85, 1.55, 1.2, 1.25], rowH: 0.4,
    border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 4.55, w: 8.0, h: 0.5, fill: { color: "FBE3DC" }, line: { color: K.verm }, rectRadius: 0.06 });
  T(s, "Time windows were tested up to 1 000 customers (Homberger, both cities). The 10 000-customer run has no time windows.",
    { x: MX + 0.2, y: 4.63, w: 7.6, h: 0.36, fontSize: 12.5, bold: true, color: K.verm, valign: "middle" });
  T(s, [
    { text: "Why distance on benchmarks? ", options: { bold: true } },
    { text: "Published reference values are distances. Same solvers; only the route cost function changes (distance, or duration with ρ(h)). Duration with traffic is run in the cities (slides 15 and 16).\n" },
    { text: "Cities: ", options: { bold: true } },
    { text: "RRNCO dataset, built on OpenStreetMap. Real road network; distances and free-flow times are shortest paths on the real graph. The hourly factor ρ(h) is our assumed profile, the same in both cities." },
  ], { x: MX, y: 5.2, w: 8.0, h: 1.65, fontSize: 11.5, paraSpaceAfter: 4 });
  card(s, 8.9, 1.5, 3.8, 5.35);
  T(s, "Road-network characteristics", { x: 9.1, y: 1.62, w: 3.5, h: 0.32, fontSize: 14, bold: true });
  T(s, "Paris", { x: 10.95, y: 2.0, w: 0.8, h: 0.25, fontSize: 10.5, bold: true, align: "right" });
  T(s, "S. Paulo", { x: 11.8, y: 2.0, w: 0.8, h: 0.25, fontSize: 10.5, bold: true, align: "right", color: K.cobalt });
  const mrow = (lab, def, a, b, y) => {
    T(s, lab, { x: 9.1, y, w: 1.9, h: 0.27, fontSize: 12, bold: true });
    T(s, a, { x: 10.85, y, w: 0.9, h: 0.27, fontSize: 12.5, bold: true, align: "right" });
    T(s, b, { x: 11.75, y, w: 0.85, h: 0.27, fontSize: 12.5, bold: true, align: "right", color: K.cobalt });
    T(s, def, { x: 9.1, y: y + 0.28, w: 3.5, h: 0.6, fontSize: 10, color: K.soft });
  };
  mrow("Mean speed", "free-flow km ÷ free-flow hours, all pairs", `${fmt(m.Paris.mean_speed_kmh)} km/h`, `${fmt(m.Sao_Paulo.mean_speed_kmh)} km/h`, 2.35);
  mrow("Circuity", "road distance ÷ straight-line distance (median, pairs over 50 m apart)", fmt(m.Paris.circuity, 2), fmt(m.Sao_Paulo.circuity, 2), 3.3);
  mrow("Asymmetry", "share of pairs where A → B and B → A differ by more than 10 m (one-way streets)", pct(m.Paris.asymmetric_pairs_pct, 0), pct(m.Sao_Paulo.asymmetric_pairs_pct, 0), 4.25);
  mrow("Area", "bounding box of the 1 000 points", `${fmt(m.Paris.area_km2, 1)} km²`, `${fmt(m.Sao_Paulo.area_km2, 1)} km²`, 5.2);
  cap(s, "Computed from the matrices; not traffic measurements.", { x: 9.1, y: 6.2, w: 3.5, h: 0.5, fontSize: 10.5 });
  s.addNotes(`PABLO (about 1.5 min).
"Each dataset answers one question. Solomon: quality and statistics at 100 customers. Homberger R1: same kind of instances with windows, 400 to 1 000 customers, still with best known values, so we can measure a gap as n grows. Synthetic uniform: 1 000 to 10 000 random customers without windows, to find the computational limit; no published optimum, so we compare to a lower bound. Paris and Sao Paulo: 999 real customers on real roads, without windows."
Red box: "Say it clearly: windows only up to 1 000 customers. We never ran 10 000 customers with windows."
"On benchmarks the objective is distance because the reference values are distances. Same solvers; only the cost function of a route changes. In the cities we also run the duration objective with traffic."
Data: RRNCO is an open dataset built on OpenStreetMap; distances and free-flow times are shortest paths on the real road graph. The hourly factor is our assumption, identical in both cities. So the city-specific part is the road geometry.
Right card: mean speed is total free-flow km divided by total free-flow time; circuity is road distance over straight-line distance (median); asymmetry is the share of pairs where A to B differs from B to A, because of one-way streets; area is the bounding box of the points. Same area, same number of customers: the differences come from the roads. We have the matrices, not the graphs, so density or degree are not measured.`);
}

// ================================================================== 11. scale chart
{
  const s = content("As n grows, every algorithm loses quality, but not at the same speed", "Round 2");
  kicker(s, "Scalability with time windows");
  tags(s, ["Homberger R1 (100: Solomon R1)", "time windows", "objective: distance", "20 s", "3 seeds", "vs best known"]);
  const R1 = { grasp: 0.68, sa: 1.59, tabu: 3.54 }; // Solomon R1 class, 100 customers, 20 s (solomon_report)
  const labels = ["100", "400", "800", "1 000"];
  s.addChart(pres.charts.LINE, ORDER.map((a) => ({ name: ALG[a].name, labels,
    values: [R1[a], ...[400, 800, 1000].map((n) => hom(a, n, 20).gap)] })), {
    x: MX, y: 1.7, w: 7.3, h: 4.6, chartColors: ORDER.map((a) => ALG[a].color), lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9,
    showTitle: true, title: "Mean gap to best known (%) against number of customers", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.0", valAxisMinVal: 0, ...chartText,
    showCatAxisTitle: true, catAxisTitle: "customers n", catAxisTitleColor: K.soft, catAxisTitleFontSize: 10,
    showValAxisTitle: true, valAxisTitle: "gap (%)", valAxisTitleColor: K.soft, valAxisTitleFontSize: 10,
  });
  cap(s, "Not the same scenario as the 10 000-customer run (slide 13): here every customer has a time window.", { x: MX, y: 6.35, w: 7.3, h: 0.5, fontSize: 11.5 });
  const g = (a) => hom(a, 1000, 20);
  const notes = [
    [K.cobalt, `GRASP-ILS  ${pct(g("grasp").gap)}`, `Best at every size. At 1 000 construction and first descent take about 2 s; perturbations fill the rest, so only one construction is made.`],
    [K.verm, `Simulated Annealing  ${pct(g("sa").gap)}`, `${fmt(g("sa").iterations / 1e6)} million moves in 20 s are only 16 000 per customer: not enough exploration yet (slide 12).`],
    [K.ochre, `Tabu Search  ${pct(g("tabu").gap)}`, `${fmt(g("tabu").routes)} trucks against ${fmt(g("grasp").routes)} for GRASP-ILS. Its start opens too many routes and its moves rarely empty one.`],
  ];
  notes.forEach(([c, h, b], i) => {
    const y = 1.7 + i * 1.6;
    card(s, 8.2, y, 4.5, 1.45);
    pill(s, 8.4, y + 0.18, h, c);
    T(s, b, { x: 8.4, y: y + 0.55, w: 4.15, h: 0.85, fontSize: 12 });
  });
  s.addNotes(`FARIDA (about 1.5 min).
Setup: Homberger R1 instances, random customers with time windows, 400, 800 and 1 000 customers; the 100 point is Solomon's R1 class. Distance objective, gap to the best known value, 20 s, 3 seeds.
"All three lose quality as n grows: same time budget, much bigger problem. But not at the same speed."
GRASP-ILS: the best at every size; at 1 000 customers it is at 9.9 %. Its construction and first descent take about 2 s; the perturbations use the rest of the 20 s, so it builds only one plan from scratch. The regret construction plus perturbations carry it.
SA: 21.8 %. 16 million moves sounds a lot, but it is 16 000 per customer against 420 000 on Solomon: it simply has not explored enough. Next slide shows that time fixes much of it.
Tabu: 37.3 %. It uses 175 trucks against 107 for GRASP-ILS. Its nearest-neighbor start opens a new route whenever a window blocks, and relocate and swap rarely empty a whole route, so the extra trucks stay. That is a structural limit, not a time limit.
Remind: this is with windows; slide 13 is a different scenario without windows.`);
}

// ================================================================== 12. convergence gif + budget
{
  const s = content("More time helps SA most; GRASP-ILS stays ahead at every budget", "Round 2");
  kicker(s, "Effect of the time budget");
  tags(s, ["Homberger R1", "1 000 customers", "time windows", "objective: distance", "20 / 60 / 120 s", "vs best known"]);
  addGif(s, "convergence_r1_10_1.gif", MX, 1.75, 7.3, 5.2 / 11, "Animation of the best gap against time for the three algorithms on 1 000 customers");
  cap(s, "Animation: one run per algorithm (60 s); best gap so far against seconds. Dashed line: 7 % target.", { x: MX, y: 5.25, w: 7.3, h: 0.3, fontSize: 11 });
  T(s, "Why three budgets? To tell apart “not enough time” from “a limit of the method”: if more time closes the gap, time was the problem.",
    { x: MX, y: 5.65, w: 7.3, h: 0.7, fontSize: 12.5, bold: true });
  const tbl = [["Mean gap, 3 seeds", "20 s", "60 s", "120 s"]].concat(ORDER.map((a) => [ALG[a].name, ...[20, 60, 120].map((t) => pct(hom(a, 1000, t).gap))]));
  s.addTable(tbl.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, fontSize: 12, fontFace: "Calibri",
    color: i === 0 ? K.white : (j === 0 ? ALG[ORDER[i - 1]].color : K.navy), fill: { color: i === 0 ? K.navy : K.white }, align: j ? "right" : "left", valign: "middle" } }))),
  { x: 8.2, y: 1.75, w: 4.5, colW: [1.95, 0.85, 0.85, 0.85], rowH: 0.4, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  const sa20 = hom("sa", 1000, 20).gap, sa120 = hom("sa", 1000, 120).gap;
  const rd = [
    [K.cobalt, "GRASP-ILS ahead at every budget", `${pct(hom("grasp", 1000, 20).gap)} → ${pct(hom("grasp", 1000, 120).gap)}: one construction, the extra time goes to perturbations.`],
    [K.verm, "SA gains the most", `${pct(sa20)} → ${pct(sa120)}, divided by ${(sa20 / sa120).toFixed(1)}: it was short of time.`],
    [K.ochre, "Tabu barely moves", `${pct(hom("tabu", 1000, 20).gap)} → ${pct(hom("tabu", 1000, 120).gap)}: its problem is the trucks.`],
  ];
  rd.forEach(([c, h, b], i) => {
    const y = 3.5 + i * 0.75;
    T(s, h, { x: 8.2, y, w: 4.5, h: 0.28, fontSize: 12.5, bold: true, color: c });
    T(s, b, { x: 8.2, y: y + 0.28, w: 4.5, h: 0.45, fontSize: 11.5 });
  });
  card(s, 8.2, 5.8, 4.5, 1.05, K.creamDeep);
  T(s, `7 % target: the brief caps the grade above a 7 to 10 % gap; we use the strict 7 %. GRASP-ILS meets it at 800 customers with 120 s (${pct(hom("grasp", 800, 120).gap)}), not at 1 000 (${pct(hom("grasp", 1000, 120).gap)}).`,
    { x: 8.35, y: 5.88, w: 4.2, h: 0.92, fontSize: 11 });
  s.addNotes(`FARIDA (about 1.5 min).
"Same 1 000-customer instances with windows, now with 20, 60 and 120 seconds. The question: is the gap a lack of time, or a limit of the method? If more time closes it, time was the problem."
Table, mean of 3 seeds: GRASP-ILS 9.9, 9.0, 7.8 %: ahead at every budget. SA 21.8, 15.0, 10.4 %: divided by 2.1, the largest gain; it was starved of time. Tabu 37.3 to 31.7 %: almost flat, because its gap is extra trucks, not missing time.
The animation is one 60 s run per algorithm: GRASP-ILS improves in rare large jumps, SA slides down continuously, Tabu flattens early.
7 % target: the brief caps the grade when the gap exceeds 7 to 10 %; we use the stricter 7 %. GRASP-ILS meets it at 800 customers with 120 s (6.7 %) but not at 1 000 (7.8 %): at 1 000 it would need more time or faster code.
Message: extra computing time does not help all algorithms equally.`);
}

// ================================================================== 13. 10 000 customers
{
  const s = content("Up to 10 000 customers without windows: who still answers?", "Round 2");
  kicker(s, "The computational limit");
  tags(s, ["synthetic uniform", "1 000 to 10 000 customers", "NO time windows", "objective: distance", "60 s (10 000: 300 s)", "1 seed", "vs radial lower bound"]);
  const sw = S.sweep || [];
  const sizes = [...new Set(sw.map((r) => r.n))].sort((a, b) => a - b);
  const at = (a, n) => sw.find((r) => r.algorithm === a && r.n === n);
  const series = ORDER.map((a) => ({ name: ALG[a].name, labels: sizes.map((n) => fmt(n)),
    values: sizes.map((n) => (at(a, n) && at(a, n).feasible ? at(a, n).vs_bound : null)) }));
  s.addChart(pres.charts.LINE, series, {
    x: MX, y: 1.7, w: 6.4, h: 3.45, chartColors: ORDER.map((a) => ALG[a].color), lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 8,
    showTitle: true, title: "% above the radial lower bound", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0", valAxisMinVal: 0, displayBlanksAs: "gap", ...chartText, titleFontSize: 12,
    showCatAxisTitle: true, catAxisTitle: "customers n", catAxisTitleColor: K.soft, catAxisTitleFontSize: 10,
  });
  card(s, MX, 5.25, 6.4, 1.6, K.navy);
  T(s, "RADIAL LOWER BOUND", { x: MX + 0.2, y: 5.33, w: 2.2, h: 0.25, fontSize: 10, bold: true, color: "F2A08A", charSpacing: 2 });
  if (has("eq_lb_white.png")) s.addImage({ path: IMG("eq_lb_white.png"), x: MX + 0.25, y: 5.65, w: 2.0, h: 0.8, altText: "LB = 2 over Q times the sum of d_0i q_i" });
  T(s, [
    { text: "d_0i depot-customer distance, q_i demand, Q capacity. A truck must reach its farthest customer and come back, and carries at most Q, so no plan can cost less.\n", options: { color: "DCE3F7" } },
    { text: "LB is not a plan and not the optimum: % above LB is not a gap to a best known value.", options: { color: "F2A08A", bold: true } },
  ], { x: MX + 2.45, y: 5.33, w: 3.85, h: 1.48, fontSize: 10.5 });
  const g = (n) => at("grasp", n), t = (n) => at("tabu", n), sa = (n) => at("sa", n);
  const big = sizes[sizes.length - 1];
  const rows = [
    ["tabu", `${pct(t(big).vs_bound)} above LB`,
      `At 10 000: ${fmt(t(big).routes)} trucks, the minimum. Neighbor lists keep one iteration cheap: ${t(1000).ms_per_iteration.toFixed(1)} ms at 1 000, ${t(big).ms_per_iteration.toFixed(1)} ms at 10 000.`],
    ["sa", `${pct(sa(big).vs_bound, 0)} above LB`,
      `At 10 000: ${fmt(sa(big).routes)} trucks. 14 million moves are 1 400 per customer: its cooling ends long before the plan is good.`],
    ["grasp", "no plan",
      `Construction plus first descent: 2 s at 1 000, 10 s at 2 000, 133 s at 5 000 (budget 60 s). At 10 000 the run passed 684 s on a 300 s budget with no plan; we stopped it.`],
  ];
  rows.forEach(([a, head, body], i) => {
    const y = 1.7 + i * 1.72;
    card(s, 7.25, y, 5.45, 1.58);
    pill(s, 7.45, y + 0.17, `${ALG[a].name}:  ${head}`, ALG[a].color);
    T(s, body, { x: 7.45, y: y + 0.55, w: 5.1, h: 1.0, fontSize: 11.5, color: K.soft });
  });
  s.addNotes(`PABLO (about 2 min).
Setup: random customers, NO time windows, distance objective; 1 000, 2 000 and 5 000 customers with 60 s, 10 000 with 300 s; one run per size (a 10 000 x 10 000 matrix takes 800 MB, on an 8 GB laptop, one at a time). These are orders of magnitude, not statistics.
No published optimum exists, so the reference is a lower bound. Bottom left: LB = 2 sum d_0i q_i / Q. Intuition: each truck must at least go to its farthest customer and back, and carries at most Q, so spreading the demand gives a minimum cost. It is NOT a feasible plan and NOT the optimum; the true optimum lies somewhere between LB and our plans. So "18.6 % above LB" is not the same thing as "18.6 % gap to the best known".
Chart: at 1 000 GRASP-ILS and Tabu tie (about 46 %); from 2 000 Tabu pulls ahead and gets closer to the bound as n grows (36, 26, 19 %); SA falls behind.
Tabu: 18.6 % above LB with 553 trucks, the minimum; its sampled neighbor lists keep an iteration at 1 to 2 ms whatever n.
SA: 84 % above LB; too few moves per customer.
GRASP-ILS: its construction plus first descent takes about 2 s at 1 000 customers, 10 s at 2 000, and 133 s at 5 000, more than the 60 s budget. At 10 000 the observed run passed 684 s on a 300 s budget without returning a plan, and we stopped it. Reason: it checks the clock only between iterations. This is a defect of the tested code; no fix was run; all numbers here come from that code. These instances are symmetric, so the 2-opt bug of slide 14 does not apply here.`);
}

// ================================================================== 14. real cities, no windows
{
  const s = content("Real roads without windows: GRASP-ILS leads at 60 s", "Round 2");
  kicker(s, "Paris and São Paulo");
  tags(s, ["RRNCO / OpenStreetMap", "999 real customers", "no time windows", "objective: distance (km)", "60 s", "5 seeds"]);
  const cities = ["Paris", "Sao_Paulo"];
  s.addChart(pres.charts.BAR, ORDER.map((a) => ({ name: ALG[a].name, labels: ["Paris", "São Paulo"], values: cities.map((c) => city(c, "distance", a).mean) })), {
    x: MX, y: 1.7, w: 6.4, h: 3.75, barDir: "col", barGapWidthPct: 60, chartColors: ORDER.map((a) => ALG[a].color),
    showTitle: true, title: "Total distance of the plan (km), mean of 5 seeds; lower is better", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", valAxisMinVal: 0, ...chartText, titleFontSize: 12,
    showValAxisTitle: true, valAxisTitle: "km", valAxisTitleColor: K.soft, valAxisTitleFontSize: 10,
  });
  card(s, MX, 5.55, 6.4, 1.3, "FBE3DC");
  T(s, [
    { text: "Correction after the review: ", options: { bold: true, color: K.verm } },
    { text: "our GRASP-ILS computed the 2-opt gain as if A → B cost the same as B → A. On one-way streets its descent cycled and wasted the minute. Fixed and rerun: a construction plus descent now takes about 2 s instead of the whole minute. Only these asymmetric city runs were affected." },
  ], { x: MX + 0.2, y: 5.62, w: 6.0, h: 1.18, fontSize: 11 });
  const ctl = (c, a, t, k) => S.cities.control.find((r) => r.city === c && r.algorithm === a && r.time_limit === t && (k === undefined || r.kicks === k));
  const dev = (c, a) => 100 * (city(c, "distance", a).mean / bestAll(c) - 1);
  const why = [
    ["Same order as Solomon", `Above the best plan of all runs: GRASP-ILS ${pct(dev("Paris", "grasp"))} and ${pct(dev("Sao_Paulo", "grasp"))}, Tabu Search ${pct(dev("Paris", "tabu"))} and ${pct(dev("Sao_Paulo", "tabu"))}, SA ${pct(dev("Paris", "sa"), 0)} and ${pct(dev("Sao_Paulo", "sa"), 0)}.`],
    ["The perturbations do the work", `Paris at 60 s with P = 0, 10, 30 perturbations: ${fmt(ctl("Paris", "grasp", 60, 0).mean, 0)}, ${fmt(ctl("Paris", "grasp", 60, 10).mean, 0)}, ${fmt(ctl("Paris", "grasp", 60, 30).mean, 0)} km. Plain GRASP is far behind.`],
    ["Five times the time", `300 s in Paris: Tabu ${fmt(ctl("Paris", "tabu", 300).mean, 0)} km, GRASP-ILS ${fmt(ctl("Paris", "grasp", 300, 90).mean, 0)} km (a tie); São Paulo: GRASP-ILS ${fmt(ctl("Sao_Paulo", "grasp", 300, 90).mean, 0)}, Tabu ${fmt(ctl("Sao_Paulo", "tabu", 300).mean, 0)} km.`],
  ];
  why.forEach(([h, b], i) => {
    const y = 1.7 + i * 1.38;
    card(s, 7.25, y, 5.45, 1.25);
    T(s, h, { x: 7.45, y: y + 0.1, w: 5.1, h: 0.32, fontSize: 13.5, bold: true });
    T(s, b, { x: 7.45, y: y + 0.45, w: 5.1, h: 0.78, fontSize: 11.5, color: K.soft });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.25, y: 5.95, w: 5.45, h: 0.9, fill: { color: K.navy }, line: { color: K.navy }, rectRadius: 0.08 });
  T(s, "France and Brazil rank the algorithms the same way; São Paulo costs more because its trips are longer and more circuitous.",
    { x: 7.45, y: 6.0, w: 5.1, h: 0.8, fontSize: 12, bold: true, color: K.white, valign: "middle" });
  s.addNotes(`DAG (about 1.5 min).
Setup: 999 real customers in Paris and Sao Paulo, road matrices from RRNCO (OpenStreetMap, shortest paths), capacity only, distance objective in km, 60 s, 5 seeds.
Correction, say it first: "In our first version Tabu Search won here. Reviewing the project we found a bug in our GRASP-ILS: its 2-opt computed the gain as if the matrix were symmetric. On one-way streets, A to B and B to A differ, so the descent applied false improvements and cycled until a cap of 100 000 moves. We fixed it, added a test, and reran: a construction plus descent now takes about 2 s instead of the whole minute. Solomon, Homberger and the synthetic instances are symmetric, so they are not affected."
Result: same order as on Solomon. GRASP-ILS about 2 to 3 % above the best plan of all runs, Tabu 5 to 10 %, SA about 32 %.
Control: with 0, 10, 30 perturbations per iteration GRASP-ILS gives 361, 335, 330 km in Paris: the perturbations are what make it strong. With 300 s Tabu and GRASP-ILS tie in Paris; GRASP-ILS stays ahead in Sao Paulo.
Same ranking in both countries; Sao Paulo costs more because its trips are longer (2.62 vs 2.49 km) and more circuitous (1.65 vs 1.51).`);
}

// ================================================================== 15. real cities with time windows
{
  const s = content("The same time windows on real roads", "Round 2");
  kicker(s, "Paris and São Paulo  |  answer to the review");
  tags(s, ["999 real customers", "windows: 120 min, 8:00 to 18:00", "service 5 min", "60 s", "5 seeds", "vs best of all runs"]);
  const w = (c, o, a) => city(c, o, a);
  const devw = (c, o, a) => {
    const best = Math.min(...S.cities.costs.filter((r) => r.city === c && r.objective === o).map((r) => r.best));
    return 100 * (w(c, o, a).mean / best - 1);
  };
  // left: CVRPTW, three algorithms
  card(s, MX, 1.7, 6.0, 3.05);
  T(s, "A. CVRPTW on real roads (ρ = 1)", { x: MX + 0.2, y: 1.78, w: 5.6, h: 0.3, fontSize: 13.5, bold: true });
  T(s, "objective: total free-flow travel time (min); all three algorithms", { x: MX + 0.2, y: 2.08, w: 5.6, h: 0.28, fontSize: 11, color: K.soft });
  const tA = [["% above best run", "Paris", "São Paulo"]].concat(ORDER.map((a) => [ALG[a].name, pct(devw("Paris", "time + windows", a)), pct(devw("Sao_Paulo", "time + windows", a))]));
  s.addTable(tA.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, fontSize: 12, fontFace: "Calibri",
    color: i === 0 ? K.white : (j === 0 ? ALG[ORDER[i - 1]].color : K.navy), fill: { color: i === 0 ? K.navy : K.white }, align: j ? "right" : "left", valign: "middle" } }))),
  { x: MX + 0.2, y: 2.45, w: 5.6, colW: [2.4, 1.6, 1.6], rowH: 0.36, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  T(s, "With windows the regret construction decides again: GRASP-ILS leads, as on Solomon and Homberger.", { x: MX + 0.2, y: 4.0, w: 5.6, h: 0.65, fontSize: 11.5, bold: true, color: K.cobalt });
  // right: full model
  card(s, 6.7, 1.7, 6.0, 3.05);
  T(s, "B. The full model: windows + hourly traffic", { x: 6.9, y: 1.78, w: 5.6, h: 0.3, fontSize: 13.5, bold: true });
  T(s, "objective: total route duration z (min), trucks leave at 08:00", { x: 6.9, y: 2.08, w: 5.6, h: 0.28, fontSize: 11, color: K.soft });
  const pil = (c, a) => S.pilot.find((r) => r.city === c && r.algorithm === a);
  const tB = [["% above best run", "999: Paris", "999: S. Paulo", "300: Paris", "300: S. Paulo"]].concat(["tabu", "grasp"].map((a) => [ALG[a].name,
    pct(devw("Paris", "duration 08:00 + windows", a)), pct(devw("Sao_Paulo", "duration 08:00 + windows", a)),
    pct(100 * (pil("Paris", a).mean / Math.min(pil("Paris", "tabu").best, pil("Paris", "grasp").best) - 1)),
    pct(100 * (pil("Sao_Paulo", a).mean / Math.min(pil("Sao_Paulo", "tabu").best, pil("Sao_Paulo", "grasp").best) - 1))]));
  s.addTable(tB.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, fontSize: 11, fontFace: "Calibri",
    color: i === 0 ? K.white : (j === 0 ? ALG[i === 1 ? "tabu" : "grasp"].color : K.navy), fill: { color: i === 0 ? K.navy : K.white }, align: j ? "right" : "left", valign: "middle" } }))),
  { x: 6.9, y: 2.45, w: 5.6, colW: [1.6, 1.0, 1.0, 1.0, 1.0], rowH: 0.36, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  T(s, "With traffic Tabu Search leads at both sizes. GRASP-ILS recomputes the duration of every candidate route: its construction and descent take 30.8 s instead of 1.9 s at 999 customers, so few perturbations fit in 60 s.",
    { x: 6.9, y: 3.75, w: 5.6, h: 0.95, fontSize: 11.5, bold: true, color: K.ochre });
  // bottom
  card(s, MX, 4.95, 6.0, 1.9, K.creamDeep);
  T(s, [
    { text: "How the windows are drawn\n", options: { bold: true, fontSize: 12.5 } },
    { text: "Depot open 08:00 to 18:00. Each customer i gets [e_i, e_i + 120 min], e_i uniform in the day, 5 min of service. A window never closes before a truck leaving at 08:00 at peak traffic (ρ = 1.80) can reach it, so every customer can be served alone: the instance is feasible. Same rule, same seed, both cities.", options: { fontSize: 11 } },
  ], { x: MX + 0.2, y: 5.03, w: 5.6, h: 1.78 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.7, y: 4.95, w: 6.0, h: 1.9, fill: { color: K.navy }, line: { color: K.navy }, rectRadius: 0.08 });
  T(s, [
    { text: "What it adds\n", options: { bold: true, fontSize: 12.5, color: "F2A08A" } },
    { text: `Routes now last about ${fmt(w("Paris", "duration 08:00 + windows", "tabu").mean / w("Paris", "duration 08:00 + windows", "tabu").routes / 60, 1)} h, and ${fmt(w("Paris", "duration 08:00 + windows", "tabu").multi_hour, 0)} of ${fmt(w("Paris", "duration 08:00 + windows", "tabu").routes, 0)} routes drive in several traffic hours: this is the test the night experiment could not give. The winner depends on the objective: static with windows, GRASP-ILS; time-dependent, Tabu Search.`, options: { fontSize: 11, color: K.white } },
  ], { x: 6.9, y: 5.03, w: 5.6, h: 1.78 });
  s.addNotes(`DAG (about 2 min). This slide answers the professor's review: "you designed the time windows, why not use them in Paris and Sao Paulo?"
How the windows are drawn: the same generator as our model. Depot open 08:00 to 18:00; each customer gets a 120-minute window starting at a uniform time in the day; 5 minutes of service; and no window closes before a truck leaving at 08:00 in peak traffic can arrive, so every customer is reachable alone and the instance is feasible. Same rule and seed in both cities.
A, left: the CVRPTW on real roads with free-flow times, all three algorithms. GRASP-ILS leads (about 3 % above the best run), Tabu 7 to 10 %, SA 21 to 23 %. With windows, the regret construction decides again, as on Solomon and Homberger.
B, right: the full model of slide 4: windows AND hourly traffic, duration objective, trucks leave at 08:00. SA has no traffic mode, so Tabu and GRASP-ILS only. Tabu leads both at 999 customers and at 300, the size of the ADEME pilot. Reason, measured: with traffic GRASP-ILS recomputes the exact duration of every candidate route in pure Python; one construction plus descent takes 30.8 s instead of 1.9 s at 999 customers (2.7 s instead of 0.2 s at 300), so few perturbations fit in the minute. Tabu Search samples 200 moves per step and caches route costs.
What it adds: routes now last several hours and every route drives through several traffic periods, which the night experiment could not test. Conclusion: the best algorithm depends on the objective. Static with windows: GRASP-ILS. With hourly traffic: Tabu Search, as implemented.`);
}

// ================================================================== 16. night
{
  const p = night("Paris"), sp = night("Sao_Paulo");
  const s = content(`Leaving at 22:00 instead of 08:00: ${fmt(p.cut, 1)} % less time on the road`, "Round 2");
  kicker(s, "Departure time");
  tags(s, ["Paris, São Paulo", "999 customers", "no time windows", "objective: duration with ρ(h)", "Tabu Search", "60 s, 5 seeds"]);
  addGif(s, "paris_day_night.gif", MX, 1.7, 7.9, 6.2 / 13.5, "Animation of trucks in Paris leaving at 08:00 and at 22:00, with a clock and the number of trucks back");
  cap(s, "Animation: one Tabu Search run per hour (30 s). Same customers, same assumed ρ(h); only the fleet departure hour changes, and each hour is optimized separately.",
    { x: MX, y: 5.35, w: 7.9, h: 0.5, fontSize: 11 });
  [["Paris", p], ["São Paulo", sp]].forEach(([c, v], i) => {
    const y = 1.7 + i * 1.7;
    card(s, 8.75, y, 3.95, 1.55);
    T(s, c, { x: 8.95, y: y + 0.1, w: 3.6, h: 0.3, fontSize: 14, bold: true });
    T(s, `−${fmt(v.cut, 1)} %`, { x: 8.95, y: y + 0.42, w: 3.6, h: 0.6, fontFace: "Cambria", fontSize: 32, bold: true, color: K.cobalt });
    T(s, `${fmt(v.day)} min at 08:00 → ${fmt(v.night)} min at 22:00`, { x: 8.95, y: y + 1.07, w: 3.6, h: 0.35, fontSize: 12, color: K.soft });
  });
  T(s, "1 − 1/ρ(8) = 1 − 1/1.80 = 44.4 %", { x: 8.75, y: 5.2, w: 3.95, h: 0.4, fontSize: 14, bold: true, fontFace: "Cambria", color: K.verm, align: "center" });
  card(s, MX, 5.95, 6.0, 0.92, "E3EBDD");
  T(s, [{ text: "What it shows: ", options: { bold: true, color: "2F6B4F" } }, { text: "the size of the assumed traffic effect on route duration: the whole saving is the 08:00 factor 1.80." }],
    { x: MX + 0.2, y: 6.0, w: 5.65, h: 0.85, fontSize: 11.5 });
  card(s, 6.7, 5.95, 6.0, 0.92, "FBE3DC");
  T(s, [{ text: "What it does not show: ", options: { bold: true, color: K.verm } }, { text: "a different visit order at night. Routes last 32 min on average: 1 of 57 changes hour, none crosses midnight. That test needs routes spanning several hours." }],
    { x: 6.9, y: 6.0, w: 5.65, h: 0.85, fontSize: 11.5 });
  s.addNotes(`DAG (about 1.5 min).
Setup: same 999 customers, same assumed profile, duration objective with traffic; the fleet leaves at 08:00 or at 22:00, and each case is optimized by Tabu Search (5 seeds, 60 s). Nothing else changes.
Result: Paris 1 831 to 1 014 minutes, -44.6 %; Sao Paulo 1 511 to 850, -43.7 %.
Say it before the professor does: this is almost exactly 1 - 1/rho(8) = 1 - 1/1.80 = 44.4 %. Why: the routes last 32 minutes on average, so nearly every leg is priced at one single factor; only 1 route of 57 changes hour and none crosses midnight. So the night just divides every trip by 1.80.
What it shows: how big the traffic effect is under our assumption. What it does NOT show: that the algorithm plans a different order at night. To test that, routes must span several hours (service times, windows over a day), so that legs fall in different hours. The model and the solvers support it; this experiment does not exercise it.
Also: the profile is assumed, and night delivery has other costs (noise, wages) the model does not price.`);
}

// ================================================================== 17. sensitivity
{
  const s = content("Each algorithm has one parameter that can break it", "Round 2");
  kicker(s, "Sensitivity analysis");
  tags(s, ["6 tuning instances", "100 customers", "time windows", "objective: distance", "3 seeds × 20 s", "vs best known"]);
  T(s, "One factor at a time: move one parameter, keep every other at its tuned value, measure the mean gap. It shows how fragile each tuned choice is. ● = value used in the campaign.",
    { x: MX, y: 1.7, w: 12.1, h: 0.45, fontSize: 12.5 });
  const panels = [
    ["tabu", "candidates", "Tabu Search: candidate list size", "moves sampled per iteration", 200],
    ["grasp", "perturb_kicks", "GRASP-ILS: perturbations per iteration", "perturbations P per iteration", 90],
    ["sa", "initial_temperature_factor", "SA: initial temperature factor", "T₀ / start cost", 0.005],
  ];
  const sv = (a, p, v) => (S.sensitivity[a] || []).find((r) => r.parameter === p && r.value === v);
  panels.forEach(([a, p, title, xt, tuned], i) => {
    const x = MX + i * 4.1;
    const cur = (S.sensitivity[a] || []).filter((r) => r.parameter === p);
    s.addChart(pres.charts.LINE, [{ name: title, labels: cur.map((r) => (r.value === tuned ? `●${r.value}` : `${r.value}`)), values: cur.map((r) => r.mean_gap) }], {
      x, y: 2.2, w: 3.9, h: 3.2, chartColors: [ALG[a].color], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 8, showLegend: false,
      showTitle: true, title, showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.0", valAxisMinVal: 0, ...chartText, titleFontSize: 12, dataLabelFontSize: 9, catAxisLabelFontSize: 9.5,
      showCatAxisTitle: true, catAxisTitle: xt, catAxisTitleColor: K.soft, catAxisTitleFontSize: 10,
      showValAxisTitle: true, valAxisTitle: "mean gap (%)", valAxisTitleColor: K.soft, valAxisTitleFontSize: 10,
    });
  });
  const reads = [
    ["tabu", `25: ${pct(sv("tabu", "candidates", 25).mean_gap)} (step almost random). 200: ${pct(sv("tabu", "candidates", 200).mean_gap)}. 800: ${pct(sv("tabu", "candidates", 800).mean_gap)} (each step 14 times slower than with 25, so far fewer steps). More is not better.`],
    ["grasp", `P = 0 (plain GRASP): ${pct(sv("grasp", "perturb_kicks", 0).mean_gap)}; P = 90: ${pct(sv("grasp", "perturb_kicks", 90).mean_gap)}. The perturbations halve the gap: the ILS part is what makes it win.`],
    ["sa", `Flat from 0.001 to 0.05 (${pct(sv("sa", "initial_temperature_factor", 0.0025).mean_gap, 2)} to ${pct(sv("sa", "initial_temperature_factor", 0.001).mean_gap, 2)}). Only near 0 (0.0005: ${pct(sv("sa", "initial_temperature_factor", 0.0005).mean_gap)}) it breaks: no worse move accepted, a plain descent.`],
  ];
  reads.forEach(([a, b], i) => {
    const x = MX + i * 4.1;
    card(s, x, 5.5, 3.9, 1.37);
    T(s, b, { x: x + 0.15, y: 5.57, w: 3.6, h: 1.25, fontSize: 11 });
  });
  s.addNotes(`DAG (about 1.5 min); each author can comment their own curve.
"Sensitivity analysis: we take the tuned setting, change ONE parameter over a range, keep all others fixed, and measure the mean gap on the 6 tuning instances (3 seeds, 20 s). It tells us how fragile each choice is." The dot marks the value used in the campaign.
Tabu, candidate list size: 25 sampled moves give 20 %, because the best of 25 random moves is almost a random step; 200 gives 2.1 %; 800 gives 7.9 %, because each iteration is 14 times slower than with 25, so in 20 s it makes far fewer steps. A U shape: more is not always better.
GRASP-ILS, perturbations P: without them (plain GRASP) 2.5 %; with 90, 1.34 %. The perturbations are what make it better.
SA, initial temperature: flat between 0.55 and 0.83 % over two orders of magnitude; it breaks only when T0 tends to 0 (2.1 %), because it then accepts no worse move and becomes a descent. SA is the most robust.
Other findings (in the notebook): Tabu tenure 35 would be better than 20 (1.43 vs 2.06 %), GRASP alpha 0.7 better than 0.3 (1.02 vs 1.34 %). We did not retune: the campaign was fixed before, and it would not change the ranking.`);
}

// ================================================================== 18. recommendation
pres.addSection({ title: "Recommendation" });
// % above the best run of a city objective (all algorithms, seeds and budgets of that objective)
const devCity = (c, o, a) => {
  const best = Math.min(...S.cities.costs.filter((r) => r.city === c && r.objective === o).map((r) => r.best),
    ...(o === "distance" ? S.cities.control.filter((r) => r.city === c).map((r) => r.best) : []));
  return 100 * (city(c, o, a).mean / best - 1);
};
const pilotGap = (c, a) => {
  const p = (x) => S.pilot.find((r) => r.city === c && r.algorithm === x);
  return 100 * (p(a).mean / Math.min(p("tabu").best, p("grasp").best) - 1);
};
const range2 = (f) => `${pct(Math.min(f("Paris"), f("Sao_Paulo")))} to ${pct(Math.max(f("Paris"), f("Sao_Paulo")))}`;
{
  const s = content("No universal winner: it depends on windows, traffic and size", "Recommendation");
  kicker(s, "Our recommendation, scenario by scenario");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 1.4, w: 12.1, h: 0.75, fill: { color: K.navy }, line: { color: K.navy }, rectRadius: 0.08 });
  T(s, [
    { text: "ADEME pilot (windows + hourly traffic)  ", options: { bold: true, color: "AEB8E6", fontSize: 12.5 } },
    { text: "Tabu Search", options: { bold: true, color: K.white, fontSize: 19, fontFace: "Cambria" } },
    { text: "      static CVRPTW (distance or free-flow time)  ", options: { bold: true, color: "AEB8E6", fontSize: 12.5 } },
    { text: "GRASP-ILS", options: { bold: true, color: K.white, fontSize: 19, fontFace: "Cambria" } },
  ], { x: MX + 0.3, y: 1.45, w: 11.5, h: 0.65, valign: "middle" });
  const rec = [
    ["About 100 customers, windows, distance", "grasp", `${pct(sol.grasp.mean, 2)} mean gap on 500 runs, significantly ahead`, "Solomon"],
    ["100 customers, a bad run is not acceptable", "sa", `best worst case (${pct(sol.sa.worst)}), every run within 7 %; robust to its parameters`, "Solomon, sensitivity"],
    ["400 to 1 000 customers, windows, distance", "grasp", `lowest gap at every size and budget; ${pct(hom("grasp", 1000, 120).gap)} at 1 000 with 120 s`, "Homberger"],
    ["999 real customers, windows, free-flow time", "grasp", `${range2((c) => devCity(c, "time + windows", "grasp"))} above the best run; Tabu ${range2((c) => devCity(c, "time + windows", "tabu"))}`, "Paris, São Paulo"],
    ["999 real customers, no windows, km", "grasp", `${range2((c) => devCity(c, "distance", "grasp"))} above the best run; Tabu ${range2((c) => devCity(c, "distance", "tabu"))}`, "Paris, São Paulo"],
    ["300 or 999 real customers, windows + hourly traffic", "tabu", `${range2((c) => pilotGap(c, "tabu"))} above the best run at 300; GRASP-ILS ${range2((c) => pilotGap(c, "grasp"))}`, "Paris, São Paulo"],
    ["2 000 to 10 000 customers, no windows", "tabu", `ahead from 2 000; ${pct(S.synthetic.tabu.vs_bound)} above the lower bound at 10 000`, "Synthetic"],
  ];
  const rows = [["Scenario", "Choose", "Because (our data)", "Evidence"]].concat(rec.map((r) => [r[0], ALG[r[1]].name, r[2], r[3]]));
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { fontSize: 11, fontFace: "Calibri", valign: "middle",
    bold: i === 0 || j === 1, color: i === 0 ? K.white : (j === 1 ? ALG[rec[i - 1][1]].color : (j === 3 ? K.soft : K.navy)),
    fill: { color: i === 0 ? K.navy : (i % 2 ? K.white : "F8F5EE") } } }))),
  { x: MX, y: 2.28, w: 12.1, colW: [3.75, 1.85, 4.85, 1.65], rowH: 0.4, border: { type: "solid", color: "E3DCCB", pt: 0.5 } });
  card(s, MX, 5.75, 5.95, 1.1, K.creamDeep);
  T(s, [
    { text: "Why no single winner: ", options: { bold: true } },
    { text: "with a static objective and windows, the regret construction and perturbations win (GRASP-ILS). When the duration depends on the hour, or n is very large, cheap iterations win (Tabu Search)." },
  ], { x: MX + 0.2, y: 5.8, w: 5.6, h: 1.0, fontSize: 11 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.75, y: 5.75, w: 5.95, h: 1.1, fill: { color: "FBE3DC" }, line: { color: K.verm }, rectRadius: 0.08 });
  T(s, [
    { text: "Caveats: ", options: { bold: true, color: K.verm } },
    { text: "no 10 000-customer test with windows; ρ(h) is assumed; the traffic verdict holds for our pure Python code at 60 s (with traffic, GRASP-ILS construction and descent are about 15 times slower)." },
  ], { x: 6.95, y: 5.8, w: 5.6, h: 1.0, fontSize: 11 });
  s.addNotes(`DAG (about 1.5 min).
"Our recommendation is a rule, not one winner, and the round 2 data changed it."
Banner: for the ADEME pilot, which has time windows AND hourly traffic with a few hundred deliveries, we recommend Tabu Search: on real roads with the full model it is ahead both at 300 and at 999 customers. For the static CVRPTW, distance or free-flow time with windows, GRASP-ILS wins everywhere we tested: Solomon, Homberger up to 1 000, and both cities.
Table, row by row: 100 customers with windows, GRASP-ILS. If one bad run is not acceptable, SA. 400 to 1 000 with windows, GRASP-ILS. Real roads with windows (free-flow time) and without windows (km), GRASP-ILS. Real roads with windows and traffic, Tabu. 2 000 to 10 000 without windows, Tabu.
Why: with a static objective, the regret construction plus perturbations is the best search. With traffic, GRASP-ILS re-evaluates every move with the exact time-dependent duration in pure Python: its construction and descent become about 15 times slower (30.8 s against 1.9 s at 999 customers), so few perturbations fit in the minute. At very large n, the same: cheap iterations win.
Caveats: no 10 000 test with windows; the traffic profile is assumed; the traffic verdict is for our implementations at 60 s. A faster time-dependent evaluation for GRASP-ILS could change it.`);
}

// ================================================================== 19. limits
{
  const s = content("What we did not solve, and what it means for the results", "Recommendation");
  kicker(s, "Limitations  |  transparency");
  const lim = [
    ["Traffic is assumed", "ρ(h) is our profile, not measured hourly data, and it is the same in Paris and São Paulo.",
      "Durations and the 44 % night saving are valid under this assumption only. Measured speeds change the matrix, not the model."],
    ["Equal time is not equal code", "SA is compiled (Numba); Tabu Search and GRASP-ILS are pure Python. Same machine, same evaluator, same wall clock.",
      "Part of each gap is implementation speed. SA still finishes 2nd on Solomon despite this advantage."],
    ["One departure time per fleet", "The model lets each truck choose its departure; the metaheuristics make all trucks leave at the same time.",
      "Our durations can only be equal to or worse than what the model allows: trucks cannot stagger to avoid the peak."],
    ["First in, first out not guaranteed", "Each trip is priced by its departure hour. 60 min free-flow: leave 08:59, ρ 1.80, arrive 10:47; leave 09:00, ρ 1.40, arrive 10:24.",
      "Waiting can pay off artificially at an hour boundary. Splitting trips at the full hour removes it."],
    ["GRASP-ILS: one bug fixed, one defect left", "Its 2-opt assumed A → B = B → A: fixed, city runs redone. It reads the clock only between iterations: 684 s on a 300 s budget at 10 000.",
      "The clock defect is not fixed; the 5 000 and 10 000 results use that code. A fix (clock checks inside construction and descent) is proposed, not run."],
    ["Brazil instead of Egypt", "Validated open road matrices existed for Paris and São Paulo; Cairo needed an OSM extraction we could not validate in time.",
      "Two countries, same protocol, but not the pair requested; no graph metrics (density, degree)."],
  ];
  lim.forEach(([h, what, cons], i) => {
    const x = MX + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 1.82;
    card(s, x, y, 5.95, 1.7);
    numDot(s, x + 0.2, y + 0.15, i + 1, K.verm, 0.32);
    T(s, h, { x: x + 0.65, y: y + 0.13, w: 5.1, h: 0.35, fontSize: 14, bold: true });
    T(s, what, { x: x + 0.25, y: y + 0.52, w: 5.5, h: 0.6, fontSize: 11 });
    T(s, [{ text: "Consequence: ", options: { bold: true, color: K.cobalt } }, { text: cons, options: { color: K.soft } }], { x: x + 0.25, y: y + 1.1, w: 5.5, h: 0.58, fontSize: 11 });
  });
  s.addNotes(`PABLO or DAG (about 1.5 min). Present this as a scientific limitations section: what we did not do, and what it changes in how to read our numbers.
1. Traffic is assumed: the profile is ours, same in both cities. Every duration result holds under that assumption; with measured speeds no equation changes, only the matrix.
2. Implementation: SA is compiled with Numba, the other two are pure Python. Same machine, same evaluator, same wall-clock budget, but not the same code speed. SA still comes second on Solomon.
3. One departure per fleet: the model allows a departure per truck; our metaheuristics fix one for all. So our durations are an upper bound of what the model permits; a 1-D search of the departure per route would close it.
4. FIFO: travel time depends only on the departure hour. Example: a 60-minute free-flow trip leaving at 8:59 is priced at 1.80, arrives 10:47; leaving at 9:00 is priced at 1.40, arrives 10:24. Leaving later arrives earlier. Fix: split each trip at the full hour.
5. GRASP-ILS: one bug fixed, one defect left. The 2-opt gain assumed a symmetric matrix; on one-way streets the descent cycled; we fixed it, added a test and redid every city run. The clock is read only between iterations; at 10 000 customers the construction and descent are longer than the budget. That defect is not fixed; the fix is proposed, not implemented or tested.
6. Brazil replaces Egypt: open validated matrices; same protocol.`);
}

// ================================================================== 20. close
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Recommendation" });
  T(s, "IN ONE SLIDE", { x: MX, y: 0.5, w: 6, h: 0.3, fontSize: 12, bold: true, color: "AEB8E6", charSpacing: 3 });
  T(s, "GRASP-ILS for routing with time windows; Tabu Search when traffic makes travel times depend on the hour",
    { x: MX, y: 0.85, w: 12.1, h: 1.2, fontFace: "Cambria", fontSize: 28, bold: true, color: K.white });
  const big = [
    [pct(sol.grasp.mean, 2), "GRASP-ILS mean gap", ["Solomon", "100 customers", "windows", "20 s", "vs best known"]],
    [pct(Math.max(devCity("Paris", "time + windows", "grasp"), devCity("Sao_Paulo", "time + windows", "grasp"))), "GRASP-ILS on real roads, at most", ["Paris, São Paulo", "999 customers", "windows", "60 s", "vs best run"]],
    [pct(Math.max(pilotGap("Paris", "tabu"), pilotGap("Sao_Paulo", "tabu"))), "Tabu Search, full model, at most", ["Paris, São Paulo", "300 customers", "windows + traffic", "60 s", "vs best run"]],
  ];
  big.forEach(([b, l, tg], i) => {
    const x = MX + i * 4.1;
    T(s, b, { x, y: 2.15, w: 3.9, h: 0.85, fontFace: "Cambria", fontSize: 44, bold: true, color: i === 2 ? "F2A08A" : K.white });
    T(s, l, { x, y: 3.0, w: 3.9, h: 0.32, fontSize: 14, bold: true, color: K.white });
    T(s, tg.join("  ·  "), { x, y: 3.33, w: 3.9, h: 0.5, fontSize: 11, color: "AEB8E6" });
  });
  T(s, "Three different settings and references: these numbers are not comparable with each other.", { x: MX, y: 3.9, w: 12.1, h: 0.3, fontSize: 12, italic: true, color: "AEB8E6" });
  const qs = [
    ["What we built", "A duration model with hourly traffic, an NP-hardness proof, an exact ILP, and three metaheuristics on one evaluator, tested from 100 to 10 000 customers."],
    ["What we learned", "Windows reward a good construction and perturbations (GRASP-ILS); traffic and very large n reward cheap iterations (Tabu Search); SA is the most robust."],
    ["What we recommend", "Tabu Search for the pilot with traffic, GRASP-ILS for static windows. Next: measured traffic, a faster time-dependent GRASP-ILS, a regret start for Tabu."],
  ];
  qs.forEach(([h, b], i) => {
    const x = MX + i * 4.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.4, w: 3.85, h: 1.85, fill: { color: "24357E" }, line: { color: "3A4C99" }, rectRadius: 0.08 });
    T(s, h, { x: x + 0.25, y: 4.5, w: 3.4, h: 0.35, fontSize: 15, bold: true, color: "F2A08A" });
    T(s, b, { x: x + 0.25, y: 4.88, w: 3.4, h: 1.3, fontSize: 12, color: K.white });
  });
  T(s, "Thank you. Questions?", { x: MX, y: 6.45, w: 8, h: 0.45, fontFace: "Cambria", fontSize: 20, italic: true, color: K.white });
  s.addNotes(`PABLO (about 1 min).
Headline: "GRASP-ILS for routing with time windows; Tabu Search when traffic makes travel times depend on the hour."
Three numbers, three DIFFERENT settings: 1.16 % is GRASP-ILS's mean gap to the best known values on 500 Solomon runs. The second is GRASP-ILS on the 999 real customers of Paris and Sao Paulo with time windows, at most that far above the best plan we found. The third is Tabu Search on 300 real customers with windows AND hourly traffic, the full model at the size of the ADEME pilot, at most that far above the best plan found. Do not compare them with each other.
What we built: a model whose objective is the total route duration with hourly traffic, the NP-hardness proof, an exact ILP to check small cases, three metaheuristics on one shared evaluator, tested from 100 to 10 000 customers.
What we learned: with windows and a static objective, the regret construction plus perturbations of GRASP-ILS wins; with traffic or at very large n, cheap iterations win, so Tabu Search; SA is the most robust to its parameters.
What we recommend: Tabu Search for the ADEME pilot, which has traffic; GRASP-ILS for static routing with windows. Next steps: measured traffic, a faster time-dependent evaluation for GRASP-ILS, a regret start for Tabu Search.
"Thank you. We are happy to take your questions."`);
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
