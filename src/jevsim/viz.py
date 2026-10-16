"""Build a self-contained HTML page from one or more spread results.

The page has the network with a step slider, the family tree of message versions, the text of
each version with the words that changed highlighted, and the per-step curves. No external
scripts, so it opens offline and inside Colab (IPython.display.HTML or an iframe).
"""

import json
from pathlib import Path

CAVEAT = ("Decisions come from Jev, a closed model reportedly trained on synthetic data. They show "
          "what the model believes about people, not how people behave.")


def build_html(results: list[dict], title: str = "How a rumor mutates") -> str:
    payload = json.dumps(results, ensure_ascii=False).replace("</", "<\\/")
    return (TEMPLATE.replace("__TITLE__", title)
            .replace("__CAVEAT__", CAVEAT)
            .replace("__DATA__", payload))


def write_html(results: list[dict], path: str | Path, title: str = "How a rumor mutates") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_html(results, title))
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root {
  --bg: #fbfaf7; --panel: #ffffff; --ink: #1d1d1f; --muted: #6b6b70; --line: #e4e2dc;
  --edge: #d6d3cc; --unexposed: #d9d6cf; --doubts: #9db4cf; --believes: #e0864a;
  --shared-ring: #1d1d1f; --hl-add: #fde7a6; --hl-del: #f3c9c3;
  --m-original: #6b6b70; --m-verbatim: #8f8f94; --m-exaggerate: #d1495b; --m-soften: #3a86c8;
  --m-add_detail: #8e5bc4; --m-change_source: #2a9d6f;
  --e-jev: #b8770b; --e-standin: #4b5563;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #17171a; --panel: #1f1f23; --ink: #ececef; --muted: #9a9aa2; --line: #2e2e34;
    --edge: #3a3a42; --unexposed: #3a3a40; --doubts: #5d7ea3; --believes: #e39a62;
    --shared-ring: #f4f4f6; --hl-add: #6b5a1f; --hl-del: #6e3a35;
    --e-jev: #e0a63c; --e-standin: #a3aab5;
  }
}
:root[data-theme="dark"] {
  --bg: #17171a; --panel: #1f1f23; --ink: #ececef; --muted: #9a9aa2; --line: #2e2e34;
  --edge: #3a3a42; --unexposed: #3a3a40; --doubts: #5d7ea3; --believes: #e39a62;
  --shared-ring: #f4f4f6; --hl-add: #6b5a1f; --hl-del: #6e3a35;
  --e-jev: #e0a63c; --e-standin: #a3aab5;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1180px; margin: 0 auto; padding: 20px 16px 40px; }
h1 { font-size: 22px; margin: 0 0 4px; }
h2 { font-size: 15px; margin: 0 0 8px; color: var(--muted); font-weight: 600; }
.caveat { color: var(--muted); font-size: 13px; margin: 0 0 16px; }
.bar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 14px; }
select, button { font: inherit; color: var(--ink); background: var(--panel);
  border: 1px solid var(--line); border-radius: 6px; padding: 4px 10px; cursor: pointer; }
input[type=range] { width: 220px; }
.grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 16px; }
@media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px; min-width: 0; }
svg { display: block; width: 100%; height: auto; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: var(--muted);
  margin-top: 8px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 50%;
  margin-right: 4px; vertical-align: -1px; }
.msg { border-left: 3px solid var(--line); padding: 6px 10px; margin: 6px 0 12px;
  background: var(--bg); border-radius: 0 6px 6px 0; }
.msg .meta { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
ins { background: var(--hl-add); text-decoration: none; border-radius: 3px; }
del { background: var(--hl-del); color: var(--muted); border-radius: 3px; }
.kv { display: grid; grid-template-columns: auto 1fr; gap: 2px 12px; font-size: 13px;
  margin-bottom: 10px; }
.kv dt { color: var(--muted); }
.kv dd { margin: 0; }
.probs { display: grid; grid-template-columns: 110px 1fr 40px; gap: 3px 8px;
  font-size: 12px; align-items: center; }
.probs .track { height: 8px; background: var(--bg); border-radius: 4px; overflow: hidden; }
.probs .fill { height: 100%; border-radius: 4px; }
.hint { color: var(--muted); font-size: 13px; }
.chain { font-size: 13px; color: var(--muted); margin-bottom: 8px; }
.chain b { color: var(--ink); font-weight: 600; }
.full { grid-column: 1 / -1; }
.summary { margin-bottom: 22px; }
.section { font-size: 17px; color: var(--ink); margin: 0 0 10px; }
.start { margin: 0 0 14px; padding: 8px 12px; border-left: 3px solid var(--m-original);
  background: var(--panel); border-radius: 0 6px 6px 0; }
</style>
</head>
<body>
<main>
  <h1>__TITLE__</h1>
  <p class="caveat">__CAVEAT__</p>
  <div class="bar">
    <select id="scenario"></select>
  </div>
  <p class="start" id="startmsg"></p>
  <div class="card summary">
    <h2>All runs of this message</h2>
    <svg id="summary" viewBox="0 0 1000 300" role="img" aria-label="Summary across runs"></svg>
    <div class="legend" id="slegend"></div>
    <p class="hint" id="snote"></p>
  </div>
  <h2 class="section">One run</h2>
  <div class="bar">
    <select id="run"></select>
    <button id="play">Play</button>
    <input id="step" type="range" min="0" max="0" value="0">
    <span id="steplabel"></span>
  </div>
  <div class="grid">
    <div class="card">
      <h2>Network</h2>
      <svg id="net" viewBox="0 0 520 520" role="img" aria-label="Contact network"></svg>
      <div class="legend">
        <span><i class="sw" style="background:var(--unexposed)"></i>not reached</span>
        <span><i class="sw" style="background:var(--doubts)"></i>reached, doubts</span>
        <span><i class="sw" style="background:var(--believes)"></i>reached, believes</span>
        <span><i class="sw" style="border:2px solid var(--shared-ring)"></i>shared</span>
      </div>
    </div>
    <div class="card" id="detail"><p class="hint">Click a person in the network or a version in the tree.</p></div>
    <div class="card full">
      <h2>Versions of the message</h2>
      <svg id="tree" viewBox="0 0 1000 260" role="img" aria-label="Family tree of message versions"></svg>
      <div class="legend" id="mlegend"></div>
    </div>
    <div class="card full">
      <h2>Per step</h2>
      <svg id="curves" viewBox="0 0 1000 240" role="img" aria-label="Metrics per step"></svg>
      <div class="legend" id="clegend"></div>
    </div>
  </div>
</main>
<script>
const RUNS = __DATA__;
const MUT = ["original","verbatim","exaggerate","soften","add_detail","change_source"];
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const mcol = m => `var(--m-${m})`;
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs = {}, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
};
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

let run, step = 0, timer = null, selected = null;

const ENGINE_COLOR = { jev: "--e-jev", standin: "--e-standin" };
const runSel = document.getElementById("run");
const scSel = document.getElementById("scenario");
const scenarios = [...new Set(RUNS.map(r => r.scenario.name))];
scenarios.forEach(sc => scSel.add(new Option(`message: ${sc}`, sc)));
scSel.onchange = () => pickScenario(scSel.value);
runSel.onchange = () => load(+runSel.value);

function pickScenario(sc) {
  runSel.innerHTML = "";
  const idx = RUNS.map((r, i) => [r, i]).filter(([r]) => r.scenario.name === sc);
  idx.sort(([a], [b]) => (a.engine > b.engine) - (a.engine < b.engine) || b.metrics.at(-1).shared - a.metrics.at(-1).shared);
  idx.forEach(([r, i]) => runSel.add(new Option(
    `${r.engine} · run ${r.run_seed} · shared ${(r.metrics.at(-1).shared * 100).toFixed(0)}%`, i)));
  document.getElementById("startmsg").innerHTML =
    `<b>Starting message</b> (from ${esc(idx[0][0].scenario.origin)}): ${esc(idx[0][0].scenario.message)}`;
  drawSummary(idx.map(([r]) => r));
  load(idx[0][1]);
}

function depthOf(V, v) { let d = 0; for (let p = v.parent; p !== null; p = V[p].parent) d++; return d; }
const mean = a => a.reduce((x, y) => x + y, 0) / a.length;
const quant = (a, q) => { const b = [...a].sort((x, y) => x - y); const i = (b.length - 1) * q;
  return b[Math.floor(i)] + (b[Math.ceil(i)] - b[Math.floor(i)]) * (i - Math.floor(i)); };

function drawSummary(runs) {
  const svg = document.getElementById("summary"); svg.innerHTML = "";
  const engines = [...new Set(runs.map(r => r.engine))].sort();
  const maxStep = Math.max(...runs.map(r => r.metrics.at(-1).step));
  const at = (r, k, s) => { const m = r.metrics.find(m => m.step === s) || r.metrics.at(-1); return m[k]; };
  const panel = (x0, w, title, ymax, ylab) => {
    el("text", { x: x0, y: 14, "font-size": 12, fill: css("--muted") }, svg).textContent = title;
    [0, 0.5, 1].forEach(t => {
      const y = 250 - t * 210;
      el("line", { x1: x0, x2: x0 + w, y1: y, y2: y, stroke: css("--line"), "stroke-dasharray": t ? "2 4" : "" }, svg);
      el("text", { x: x0 - 5, y: y + 4, "text-anchor": "end", "font-size": 11, fill: css("--muted") }, svg).textContent = ylab(t * ymax);
    });
    return v => 250 - v / ymax * 210;
  };
  // Panel 1: share of people who shared, mean and middle 50% of runs, per step
  const X1 = s => 40 + s / maxStep * 260, Y1 = panel(40, 260, "shared, by step (line = mean, band = middle half of runs)", 1, t => `${(t * 100).toFixed(0)}%`);
  for (let s = 0; s <= maxStep; s += Math.max(1, Math.ceil(maxStep / 8)))
    el("text", { x: X1(s), y: 268, "text-anchor": "middle", "font-size": 11, fill: css("--muted") }, svg).textContent = s;
  for (const e of engines) {
    const rs = runs.filter(r => r.engine === e), c = css(ENGINE_COLOR[e] || "--ink");
    const steps = [...Array(maxStep + 1).keys()];
    const lo = steps.map(s => quant(rs.map(r => at(r, "shared", s)), 0.25));
    const hi = steps.map(s => quant(rs.map(r => at(r, "shared", s)), 0.75));
    el("polygon", { points: steps.map(s => `${X1(s)},${Y1(hi[s])}`).concat(steps.slice().reverse().map(s => `${X1(s)},${Y1(lo[s])}`)).join(" "),
      fill: c, opacity: 0.15 }, svg);
    el("polyline", { points: steps.map(s => `${X1(s)},${Y1(mean(rs.map(r => at(r, "shared", s))))}`).join(" "),
      fill: "none", stroke: c, "stroke-width": 2.2 }, svg);
  }
  // Panel 2: final reach and belief per run, one dot per run
  const X2 = 380, Y2 = panel(X2, 230, "end of run: shared and believe (one dot per run)", 1, t => `${(t * 100).toFixed(0)}%`);
  engines.forEach((e, k) => {
    const rs = runs.filter(r => r.engine === e), c = css(ENGINE_COLOR[e] || "--ink");
    [["shared", 0], ["believe", 1]].forEach(([key, j]) => {
      const cx = X2 + 30 + j * 115 + k * 40;
      rs.forEach((r, i) => el("circle", { cx: cx + ((i * 37) % 17 - 8), cy: Y2(r.metrics.at(-1)[key]), r: 3,
        fill: c, opacity: 0.6 }, svg));
      const m = mean(rs.map(r => r.metrics.at(-1)[key]));
      el("line", { x1: cx - 13, x2: cx + 13, y1: Y2(m), y2: Y2(m), stroke: c, "stroke-width": 3 }, svg);
    });
  });
  ["shared", "believe"].forEach((l, j) => el("text", { x: X2 + 50 + j * 115, y: 268, "text-anchor": "middle", "font-size": 11, fill: css("--muted") }, svg).textContent = l);
  // Panel 3: extremity of versions by generation (distance from the original)
  const maxD = Math.max(1, ...runs.flatMap(r => r.variants.map(v => depthOf(r.variants, v))));
  const X3 = d => 690 + d / maxD * 280, Y3 = panel(690, 280, "extremity of versions by generation (0 to 4)", 4, t => t.toFixed(0));
  for (let d = 0; d <= maxD; d += Math.max(1, Math.ceil(maxD / 8)))
    el("text", { x: X3(d), y: 268, "text-anchor": "middle", "font-size": 11, fill: css("--muted") }, svg).textContent = d;
  const notes = [];
  for (const e of engines) {
    const rs = runs.filter(r => r.engine === e), c = css(ENGINE_COLOR[e] || "--ink");
    const byD = {};
    rs.forEach(r => r.variants.forEach(v => { if (v.extremity !== null) (byD[depthOf(r.variants, v)] ||= []).push(v.extremity); }));
    const ds = Object.keys(byD).map(Number).sort((a, b) => a - b).filter(d => byD[d].length >= 3);
    el("polyline", { points: ds.map(d => `${X3(d)},${Y3(mean(byD[d]))}`).join(" "), fill: "none", stroke: c, "stroke-width": 2.2 }, svg);
    ds.forEach(d => el("circle", { cx: X3(d), cy: Y3(mean(byD[d])), r: 2 + Math.sqrt(byD[d].length), fill: c, opacity: 0.8 }, svg));
    const muts = {}; rs.forEach(r => r.events.forEach(ev => { if (ev.shares) muts[ev.mutation] = (muts[ev.mutation] || 0) + 1; }));
    const tot = Object.values(muts).reduce((a, b) => a + b, 0) || 1;
    notes.push(`<b>${e}</b> (${rs.length} runs): ` + Object.entries(muts).sort((a, b) => b[1] - a[1])
      .map(([m, n]) => `${m.replace("_", " ")} ${(n / tot * 100).toFixed(0)}%`).join(", "));
  }
  document.getElementById("slegend").innerHTML = engines.map(e =>
    `<span><i class="sw" style="background:var(${ENGINE_COLOR[e] || "--ink"})"></i>${e}</span>`).join("") +
    "<span>generation = rewrites since the original; dot size = number of versions (shown when at least 3)</span>";
  document.getElementById("snote").innerHTML = "How sharers changed the message: " + notes.join(" · ");
}
const slider = document.getElementById("step");
slider.oninput = () => { step = +slider.value; draw(); };
document.getElementById("play").onclick = () => {
  if (timer) { clearInterval(timer); timer = null; return setPlay(false); }
  if (step >= +slider.max) step = 0;
  setPlay(true);
  timer = setInterval(() => {
    step++; slider.value = step; draw();
    if (step >= +slider.max) { clearInterval(timer); timer = null; setPlay(false); }
  }, 900);
};
const setPlay = on => document.getElementById("play").textContent = on ? "Pause" : "Play";

function load(i) {
  run = RUNS[i];
  run.reach = {};
  run.events.forEach(e => { run.reach[e.variant] = (run.reach[e.variant] || 0) + 1; });
  slider.max = run.metrics[run.metrics.length - 1].step;
  step = +slider.max; slider.value = step; selected = null;
  document.getElementById("detail").innerHTML = '<p class="hint">Click a person in the network or a version in the tree.</p>';
  draw();
}

function nodeAt(s) {  // state of every node after step s
  const st = run.nodes.map(() => ({ reached: false, belief: null, shared: false, received: null, forwarded: null }));
  for (const e of run.events) {
    if (e.step > s) continue;
    const n = st[e.node];
    n.reached = true;
    if (e.kind === "seed") { n.belief = 0.9; n.shared = true; n.received = n.forwarded = 0; continue; }
    n.belief = e.belief; n.received = e.variant;
    if (e.shares) { n.shared = true; n.forwarded = e.forwarded; }
  }
  return st;
}

function draw() {
  document.getElementById("steplabel").textContent = `step ${step} of ${slider.max}`;
  drawNet(); drawTree(); drawCurves();
}

function drawNet() {
  const svg = document.getElementById("net"); svg.innerHTML = "";
  const xs = run.graph.nodes.map(n => n.x), ys = run.graph.nodes.map(n => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const P = n => [30 + (n.x - x0) / (x1 - x0) * 460, 30 + (n.y - y0) / (y1 - y0) * 460];
  const pos = run.graph.nodes.map(P);
  const st = nodeAt(step);
  const passed = new Set(run.events.filter(e => e.from !== null && e.from !== undefined && e.step <= step)
    .map(e => [Math.min(e.from, e.node), Math.max(e.from, e.node)].join("-")));
  const fresh = new Set(run.events.filter(e => e.from !== null && e.from !== undefined && e.step === step)
    .map(e => [Math.min(e.from, e.node), Math.max(e.from, e.node)].join("-")));
  for (const e of run.graph.edges) {
    const k = [Math.min(e.a, e.b), Math.max(e.a, e.b)].join("-");
    const [a, b] = [pos[e.a], pos[e.b]];
    el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1],
      stroke: fresh.has(k) ? css("--believes") : passed.has(k) ? css("--muted") : css("--edge"),
      "stroke-width": fresh.has(k) ? 2.5 : passed.has(k) ? 1.4 : 1,
      "stroke-dasharray": e.kind === "long" ? "4 4" : "" }, svg);
  }
  run.nodes.forEach((n, i) => {
    const s = st[i], [x, y] = pos[i];
    const fill = !s.reached ? css("--unexposed") : s.belief > 0.5 ? css("--believes") : css("--doubts");
    const g = el("g", { style: "cursor:pointer" }, svg);
    if (s.shared) el("circle", { cx: x, cy: y, r: 13, fill: "none", stroke: s.forwarded !== null ? css(`--m-${run.variants[s.forwarded].mutation}`) : css("--shared-ring"), "stroke-width": 3 }, g);
    el("circle", { cx: x, cy: y, r: i === selected ? 10 : 8, fill, stroke: i === selected ? css("--ink") : "none", "stroke-width": 2 }, g);
    if (i === run.seed_node) el("text", { x, y: y - 16, "text-anchor": "middle", "font-size": 11, fill: css("--muted") }, g).textContent = "start";
    const t = el("title", {}, g); t.textContent = `${n.name}${s.reached ? ` · belief ${(s.belief ?? 0).toFixed(2)}` : ""}`;
    g.onclick = () => { selected = i; showNode(i); drawNet(); };
  });
}

function wordDiff(a, b) {  // highlight words of b that are not in a (LCS on words)
  const A = a.split(/(\s+)/).filter(w => w.trim()), B = b.split(/(\s+)/).filter(w => w.trim());
  const norm = w => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
  const m = A.length, n = B.length, L = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = m - 1; i >= 0; i--) for (let j = n - 1; j >= 0; j--)
    L[i][j] = norm(A[i]) === norm(B[j]) ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const out = []; let i = 0, j = 0;
  while (i < m && j < n) {
    if (norm(A[i]) === norm(B[j])) { out.push(esc(B[j])); i++; j++; }
    else if (L[i + 1][j] >= L[i][j + 1]) { out.push(`<del>${esc(A[i])}</del>`); i++; }
    else { out.push(`<ins>${esc(B[j])}</ins>`); j++; }
  }
  while (i < m) out.push(`<del>${esc(A[i++])}</del>`);
  while (j < n) out.push(`<ins>${esc(B[j++])}</ins>`);
  return out.join(" ");
}

function lineage(vid) {
  const chain = [];
  for (let v = run.variants[vid]; v; v = v.parent === null ? null : run.variants[v.parent]) chain.unshift(v);
  return chain;
}

function msgBlock(v, label) {
  const parent = v.parent === null ? null : run.variants[v.parent];
  const author = v.author === null ? "original" : run.nodes[v.author].name;
  const scores = v.emotion === null ? "" : ` · emotion ${v.emotion.toFixed(1)}/4 · extremity ${v.extremity.toFixed(1)}/4`;
  return `<div class="msg" style="border-left-color:${mcol(v.mutation)}">
    <div class="meta">${label} · version ${v.id} · ${v.mutation.replace("_", " ")} by ${esc(author)} at step ${v.step}${scores}</div>
    ${parent ? wordDiff(parent.text, v.text) : esc(v.text)}</div>`;
}

function probBars(p) {
  return `<div class="probs">${Object.entries(p).map(([k, v]) =>
    `<span>${k.replace("_", " ")}</span><span class="track"><span class="fill" style="display:block;width:${(v * 100).toFixed(0)}%;background:${mcol(k)}"></span></span><span>${v.toFixed(2)}</span>`).join("")}</div>`;
}

function showNode(i) {
  const n = run.nodes[i];
  const ev = run.events.filter(e => e.node === i);
  const last = ev[ev.length - 1];
  let h = `<h2>${esc(n.name)}</h2><dl class="kv">
    <dt>prior belief</dt><dd>${n.prior.toFixed(2)}</dd>
    <dt>view on the topic</dt><dd>${n.stance ?? "none"}</dd>`;
  if (!last) return document.getElementById("detail").innerHTML = h + `</dl><p class="hint">Never reached.</p>`;
  if (last.kind === "seed") {
    h += `</dl><p class="hint">Started the rumor by forwarding the original.</p>` + msgBlock(run.variants[0], "forwarded");
  } else {
    h += `<dt>reached at step</dt><dd>${ev[0].step}, from ${esc(run.nodes[last.from].name)}</dd>
      <dt>P(believes)</dt><dd>${last.belief.toFixed(2)} → ${last.believes ? "believes" : "doubts"}</dd>
      <dt>P(shares)</dt><dd>${last.p_share.toFixed(2)} → ${last.shares ? "shared" : "did not share"}</dd></dl>`;
    h += msgBlock(run.variants[last.variant], "received");
    if (last.shares) {
      h += `<div class="hint">How Jev expected them to rewrite it (one was drawn: <b>${last.mutation.replace("_", " ")}</b>)</div>` + probBars(last.mutation_probs);
      if (last.forwarded !== last.variant) h += msgBlock(run.variants[last.forwarded], "forwarded");
      else h += `<p class="hint">Forwarded it unchanged.</p>`;
    }
  }
  document.getElementById("detail").innerHTML = h;
}

function showVariant(vid) {
  const chain = lineage(vid);
  let h = `<h2>Version ${vid} and its ancestors</h2><div class="chain">${chain.map(v =>
    `<b>v${v.id}</b> ${v.mutation.replace("_", " ")}`).join(" → ")}</div>`;
  h += chain.slice().reverse().map((v, k) => msgBlock(v, k === 0 ? "this version" : "ancestor")).join("");
  h += `<p class="hint">Received by ${run.reach[vid] || 0} people.</p>`;
  document.getElementById("detail").innerHTML = h;
}

function drawTree() {
  const svg = document.getElementById("tree"); svg.innerHTML = "";
  const V = run.variants, maxStep = Math.max(1, +slider.max);
  const kids = {}; V.forEach(v => { if (v.parent !== null) (kids[v.parent] ||= []).push(v.id); });
  let row = 0; const y = {};
  (function place(id) {  // leaves get consecutive rows, parents sit at the mean of their children
    const c = kids[id] || [];
    if (!c.length) { y[id] = row++; return; }
    c.forEach(place); y[id] = c.reduce((s, k) => s + y[k], 0) / c.length;
  })(0);
  const H = Math.max(260, row * 34 + 40);
  svg.setAttribute("viewBox", `0 0 1000 ${H}`);
  const X = s => 30 + s / maxStep * 700, Y = r => 24 + r * ((H - 48) / Math.max(1, row - 1 || 1));
  for (let s = 0; s <= maxStep; s++) {
    el("line", { x1: X(s), x2: X(s), y1: 8, y2: H - 8, stroke: css("--line") }, svg);
    el("text", { x: X(s), y: H - 1, "text-anchor": "middle", "font-size": 11, fill: css("--muted") }, svg).textContent = `step ${s}`;
  }
  V.forEach(v => {
    if (v.parent === null) return;
    const p = V[v.parent];
    el("path", { d: `M${X(p.step)},${Y(y[p.id])} C${(X(p.step) + X(v.step)) / 2},${Y(y[p.id])} ${(X(p.step) + X(v.step)) / 2},${Y(y[v.id])} ${X(v.step)},${Y(y[v.id])}`,
      fill: "none", stroke: v.step <= step ? css("--muted") : css("--line"), "stroke-width": 1.5 }, svg);
  });
  V.forEach(v => {
    const visible = v.step <= step;
    const g = el("g", { style: "cursor:pointer", opacity: visible ? 1 : 0.25 }, svg);
    const r = 6 + Math.sqrt(run.reach[v.id] || 0) * 2.5;
    el("circle", { cx: X(v.step), cy: Y(y[v.id]), r, fill: css(`--m-${v.mutation}`) }, g);
    // Only versions with no descendants get a text label; the others would run into their
    // children on the same row. Click any version to read it in full.
    const leaf = !(kids[v.id] || []).length;
    // Fit the label in the space left before the right edge (about 6.5 px per character).
    const room = Math.max(4, Math.floor((995 - X(v.step) - r - 5) / 6.5) - 4);
    const words = v.text.length > room ? v.text.slice(0, room - 1).trimEnd() + "…" : v.text;
    el("text", leaf ? { x: X(v.step) + r + 5, y: Y(y[v.id]) + 4, "font-size": 12, fill: css("--ink") }
                    : { x: X(v.step), y: Y(y[v.id]) - r - 4, "text-anchor": "middle", "font-size": 11, fill: css("--muted") },
       g).textContent = leaf ? `v${v.id} ${words}` : `v${v.id}`;
    const t = el("title", {}, g); t.textContent = v.text;
    g.onclick = () => showVariant(v.id);
  });
  document.getElementById("mlegend").innerHTML = MUT.filter(m => m !== "verbatim").map(m =>
    `<span><i class="sw" style="background:${mcol(m)}"></i>${m.replace("_", " ")}</span>`).join("") +
    `<span>circle size = people who received it</span>`;
}

function drawCurves() {
  const svg = document.getElementById("curves"); svg.innerHTML = "";
  const M = run.metrics, maxStep = Math.max(1, M[M.length - 1].step);
  const X = s => 50 + s / maxStep * 420, Y = v => 200 - v * 170;
  const X2 = s => 560 + s / maxStep * 420, Y2 = v => 200 - v / 4 * 170;
  const axis = (x0, label, ticks, fy) => {
    el("line", { x1: x0, x2: x0 + 420, y1: 200, y2: 200, stroke: css("--line") }, svg);
    ticks.forEach(t => {
      el("line", { x1: x0, x2: x0 + 420, y1: fy(t), y2: fy(t), stroke: css("--line"), "stroke-dasharray": "2 4" }, svg);
      el("text", { x: x0 - 6, y: fy(t) + 4, "text-anchor": "end", "font-size": 11, fill: css("--muted") }, svg).textContent = label(t);
    });
    for (let s = 0; s <= maxStep; s++) el("text", { x: x0 + s / maxStep * 420, y: 218, "text-anchor": "middle", "font-size": 11, fill: css("--muted") }, svg).textContent = s;
  };
  axis(50, t => `${t * 100}%`, [0, 0.5, 1], Y);
  axis(560, t => t, [0, 2, 4], Y2);
  el("text", { x: 50, y: 14, "font-size": 12, fill: css("--muted") }, svg).textContent = "share of all 64 people";
  el("text", { x: 560, y: 14, "font-size": 12, fill: css("--muted") }, svg).textContent = "versions shared that step, mean score (0 to 4)";
  const series = [
    ["exposed", "reached", "--doubts", X, Y], ["believe", "believe (P > 0.5)", "--believes", X, Y],
    ["shared", "shared", "--ink", X, Y], ["emotion", "emotion", "--m-exaggerate", X2, Y2],
    ["extremity", "extremity", "--m-add_detail", X2, Y2],
  ];
  for (const [k, , c, fx, fy] of series) {
    const pts = M.filter(m => m[k] !== null && m[k] !== undefined);
    if (!pts.length) continue;
    el("polyline", { points: pts.map(m => `${fx(m.step)},${fy(m[k])}`).join(" "), fill: "none", stroke: css(c), "stroke-width": 2 }, svg);
    pts.forEach(m => el("circle", { cx: fx(m.step), cy: fy(m[k]), r: m.step === step ? 4.5 : 2.5, fill: css(c) }, svg));
  }
  el("line", { x1: X(step), x2: X(step), y1: 24, y2: 200, stroke: css("--muted"), "stroke-dasharray": "3 3" }, svg);
  el("line", { x1: X2(step), x2: X2(step), y1: 24, y2: 200, stroke: css("--muted"), "stroke-dasharray": "3 3" }, svg);
  document.getElementById("clegend").innerHTML = series.map(([, l, c]) =>
    `<span><i class="sw" style="background:var(${c})"></i>${l}</span>`).join("");
}

pickScenario(scenarios[0]);
</script>
</body>
</html>
"""
