/* FounderOS landing: animated founder-graph preview + hand-off of the first thought to the workspace. */
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const C = { root: "#8fb0ff", build: "#74a6ff", money: "#e6b85c", people: "#b79cff", market: "#78d2a1", legal: "#ff7f7f" };
  const N = [
    ["root", "PulseSense", "root", null, 3], ["product", "Product", "build", "root", 2], ["money", "Money", "money", "root", 2], ["people", "People", "people", "root", 2],
    ["market", "Market", "market", "root", 2], ["legal", "Legal", "legal", "root", 2],
    ["sensor", "Sensor", "build", "product", 1], ["mvp", "MVP", "build", "product", 1], ["launch", "Launch", "build", "product", 1],
    ["runway", "Runway", "money", "money", 1], ["funding", "Funding", "money", "money", 1],
    ["cto", "CTO Hire", "people", "people", 1], ["hospitals", "Hospitals", "market", "market", 1], ["compliance", "Compliance", "legal", "legal", 1],
  ];
  const X = [["cto", "mvp"], ["runway", "cto"], ["hospitals", "mvp"], ["compliance", "launch"], ["funding", "hospitals"]];
  const W = 640, H = 540;
  const el = (t, a = {}, txt) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; return e; };
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // deterministic layout: small force simulation, run once up front
  function layout() {
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const P = {}; N.forEach((n, i) => { const a = rnd() * 6.283, r = n[3] === null ? 0 : n[3] === "root" ? 120 : 190; P[n[0]] = { x: Math.cos(a) * r, y: Math.sin(a) * r, vx: 0, vy: 0 }; });
    const E = N.filter(n => n[3]).map(n => [n[0], n[3], n[3] === "root" ? 118 : 78, 0.06]).concat(X.map(([a, b]) => [a, b, 190, 0.012]));
    for (let it = 0; it < 500; it++) {
      const ids = Object.keys(P);
      for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
        const a = P[ids[i]], b = P[ids[j]]; let dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy + 40, d = Math.sqrt(d2), f = 5200 / d2;
        a.vx += dx / d * f; a.vy += dy / d * f; b.vx -= dx / d * f; b.vy -= dy / d * f;
      }
      E.forEach(([s, t, len, k]) => { const a = P[s], b = P[t]; const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, f = (d - len) * k; a.vx += dx / d * f; a.vy += dy / d * f; b.vx -= dx / d * f; b.vy -= dy / d * f; });
      ids.forEach(id => { const p = P[id]; if (id === "root") { p.x = p.y = 0; return; } p.vx -= p.x * 0.004; p.vy -= p.y * 0.004; p.x += p.vx * 0.5; p.y += p.vy * 0.5; p.vx *= 0.8; p.vy *= 0.8; });
    }
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; Object.values(P).forEach(p => { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); });
    const k = Math.min((W - 150) / (x1 - x0 || 1), (H - 90) / (y1 - y0 || 1)), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    Object.values(P).forEach(p => { p.x = W / 2 + (p.x - cx) * k; p.y = H / 2 + (p.y - cy) * k; });
    return P;
  }

  function buildPreview() {
    const svg = document.getElementById("previewGraph"); if (!svg) return;
    const P = layout(), edges = [], nodes = {};
    const curve = (a, b, bend) => { const dx = b.x - a.x, dy = b.y - a.y, l = Math.hypot(dx, dy) || 1; return `M${a.x.toFixed(1)} ${a.y.toFixed(1)} Q${((a.x + b.x) / 2 - dy / l * bend).toFixed(1)} ${((a.y + b.y) / 2 + dx / l * bend).toFixed(1)} ${b.x.toFixed(1)} ${b.y.toFixed(1)}`; };
    const gE = el("g"), gN = el("g"); svg.append(gE, gN);
    N.filter(n => n[3]).forEach(n => { const p = el("path", { class: "pg-edge pg-struct", d: curve(P[n[3]], P[n[0]], 10) }); p.dataset.a = n[3]; p.dataset.b = n[0]; p.dataset.kind = n[3] === "root" ? "s1" : "s2"; gE.appendChild(p); edges.push(p); });
    X.forEach(([a, b], i) => { const p = el("path", { class: "pg-edge pg-cross", "stroke-dasharray": "6 6", d: curve(P[a], P[b], 34 + i * 6) }); p.dataset.a = a; p.dataset.b = b; p.dataset.kind = "x"; gE.appendChild(p); edges.push(p); });
    N.forEach(n => {
      const r = n[4] === 3 ? 20 : n[4] === 2 ? 14 : 8, col = C[n[2]] || C.root;
      const g = el("g", { class: "pg-node " + (n[4] === 3 ? "root" : n[4] === 1 ? "leaf" : ""), transform: `translate(${P[n[0]].x.toFixed(1)} ${P[n[0]].y.toFixed(1)})`, style: "--c:" + col });
      const inner = el("g", { class: "pg-float", style: "animation-delay:" + (-(n[0].length * 0.7) % 7).toFixed(1) + "s" });
      inner.append(el("circle", { r }), el("text", { x: 0, y: r + 15, "text-anchor": "middle" }, n[1]));
      g.appendChild(inner); g.dataset.id = n[0]; gN.appendChild(g); nodes[n[0]] = g;
      g.addEventListener("pointerenter", () => hover(n[0])); g.addEventListener("pointerleave", () => hover(null));
    });
    function hover(id) {
      svg.classList.toggle("has-hv", !!id); if (!id) { svg.querySelectorAll(".lit").forEach(e => e.classList.remove("lit")); return; }
      const nb = new Set([id]); edges.forEach(e => { const on = e.dataset.a === id || e.dataset.b === id; e.classList.toggle("lit", on); if (on) { nb.add(e.dataset.a); nb.add(e.dataset.b); } });
      Object.keys(nodes).forEach(k => nodes[k].classList.toggle("lit", nb.has(k)));
    }
    const show = (e, on = true) => { if (e.classList.contains("pg-node")) e.classList.toggle("in", on); else { e.style.opacity = on ? "1" : "0"; if (e.dataset.kind === "x") e.style.opacity = "1"; } };
    const steps = [
      () => nodes.root.classList.add("in"),
      () => edges.filter(e => e.dataset.kind === "s1").forEach((e, i) => setTimeout(() => { e.style.opacity = "1"; nodes[e.dataset.b].classList.add("in"); }, i * 140)),
      () => edges.filter(e => e.dataset.kind === "s2").forEach((e, i) => setTimeout(() => { e.style.opacity = "1"; nodes[e.dataset.b].classList.add("in"); }, i * 110)),
      () => edges.filter(e => e.dataset.kind === "x").forEach((e, i) => setTimeout(() => { e.style.opacity = "1"; }, i * 520)),
    ];
    if (reduced) { Object.values(nodes).forEach(n => n.classList.add("in")); edges.forEach(e => (e.style.opacity = "1")); return; }
    const gaps = [250, 900, 1300, 0]; let t = 300; steps.forEach((s, i) => { setTimeout(s, t); t += gaps[i]; });
  }

  const EXAMPLE = "We're building a wearable heart-rate monitor called PulseSense. I need to validate customers and understand the regulatory requirements. We need engineering help, runway is limited and I'm considering fundraising. I'm not sure whether to build the prototype first or talk to hospitals.";
  function wire() {
    const form = document.getElementById("seedForm"), ta = document.getElementById("seedText");
    form.addEventListener("submit", e => { e.preventDefault(); const t = ta.value.trim(); try { if (t) sessionStorage.setItem("fos_seed", t.slice(0, 12000)); } catch (err) { /* private mode: user can paste in the workspace */ } location.href = "/app"; });
    document.getElementById("seedExample").addEventListener("click", () => { ta.value = EXAMPLE; ta.focus(); });
    const top = document.getElementById("toTop"); if (top) top.addEventListener("click", () => setTimeout(() => ta.focus({ preventScroll: true }), 400));
  }
  document.addEventListener("DOMContentLoaded", () => { try { buildPreview(); } catch (e) { console.error("preview failed", e); } wire(); });
})();