const FounderGraph = (() => {
  const $ = id => document.getElementById(id);
  let graph = { root: { title: "Your startup", summary: "" }, nodes: [], edges: [], insights: [], questions: [] };

  const labels = {
    goal:"Goal", idea:"Idea", initiative:"Initiative", problem:"Problem", customer:"Customer",
    product:"Product", market:"Market", decision:"Decision", option:"Option", risk:"Risk",
    dependency:"Dependency", constraint:"Constraint", fact:"Fact", assumption:"Assumption",
    metric:"Metric", experiment:"Experiment", unknown:"Unknown", investment:"Investment",
    cost:"Cost", revenue:"Revenue", runway:"Runway"
  };

  async function load() {
    try {
      graph = await API.getGraph();
      render();
    } catch (e) {
      graph = { root:{title:"Your startup",summary:""}, nodes:[], edges:[], insights:[], questions:[] };
      render();
    }
  }

  function makeSvg(tag, attrs = {}, text = "") {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v));
    if (text) el.textContent = text;
    return el;
  }

  function buildTree(nodes, edges) {
    const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
    const parent = {};
    (edges || []).forEach(e => {
      if (!byId[e.source] || !byId[e.target] || parent[e.source] || parent[e.target]) return;
      if (e.relationship === "depends_on") parent[e.source] = e.target;
      else if (["supports","unlocks","causes","measures","tests"].includes(e.relationship)) parent[e.target] = e.source;
      else if (e.relationship === "conflicts_with" || e.relationship === "alternative_to") parent[e.target] = e.source;
    });

    nodes.forEach(n => {
      const seen = new Set([n.id]);
      let p = parent[n.id];
      while (p) {
        if (seen.has(p)) { delete parent[n.id]; break; }
        seen.add(p);
        p = parent[p];
      }
    });

    const levels = {};
    const queue = nodes.filter(n => !parent[n.id]).map(n => [n.id, 1]);
    while (queue.length) {
      const item = queue.shift();
      const id = item[0], level = item[1];
      levels[id] = Math.min(level, 4);
      edges.forEach(e => {
        if (e.source === id && !levels[e.target]) queue.push([e.target, level + 1]);
        if (e.target === id && !levels[e.source]) queue.push([e.source, level + 1]);
      });
    }
    nodes.forEach(n => { if (!levels[n.id]) levels[n.id] = 1; });

    const pos = {};
    const buckets = {1:[],2:[],3:[],4:[]};
    nodes.forEach(n => buckets[levels[n.id]].push(n));
    const xs = {1:300, 2:545, 3:775, 4:980};
    [1,2,3,4].forEach(level => {
      const bucket = buckets[level];
      bucket.forEach((n, i) => {
        const step = 540 / Math.max(1, bucket.length);
        pos[n.id] = { x:xs[level], y:70 + step * (i + 0.5) };
      });
    });
    return { parent, levels, pos };
  }

  function render() {
    const svg = $("founderGraphSvg");
    if (!svg) return;
    const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
    const edges = Array.isArray(graph.edges) ? graph.edges : [];
    const empty = $("graphEmpty");
    if (empty) empty.hidden = nodes.length > 0;
    svg.innerHTML = "";

    const tree = buildTree(nodes, edges);
    const pos = tree.pos, parent = tree.parent;
    const rootX = 64, rootY = 340;

    svg.appendChild(makeSvg("path", { d:"M 98 340 C 145 340 175 340 242 340", class:"root-trunk" }));

    nodes.filter(n => !parent[n.id]).forEach(n => {
      const p = pos[n.id];
      if (!p) return;
      svg.appendChild(makeSvg("path", {
        d:"M 98 340 C 150 340 185 " + p.y + " " + (p.x - 58) + " " + p.y,
        class:"mind-edge branch-" + String(n.type || "idea").replace(/[^a-z0-9_-]/gi,"")
      }));
    });

    edges.forEach(e => {
      const a = pos[e.source], b = pos[e.target];
      if (!a || !b || parent[e.source] === e.target || parent[e.target] === e.source) return;
      svg.appendChild(makeSvg("path", {
        d:"M " + (a.x + 54) + " " + a.y + " C " + ((a.x+b.x)/2) + " " + a.y + " " + ((a.x+b.x)/2) + " " + b.y + " " + (b.x-54) + " " + b.y,
        class:"mind-edge cross-link " + (e.relationship || "")
      }));
    });

    const rootGroup = makeSvg("g", { class:"mind-root" });
    rootGroup.appendChild(makeSvg("circle", { cx:rootX, cy:rootY, r:34 }));
    rootGroup.appendChild(makeSvg("text", { x:rootX, y:rootY-2, class:"root-title" }, (graph.root && graph.root.title || "Your startup").slice(0,18)));
    rootGroup.appendChild(makeSvg("text", { x:rootX, y:rootY+14, class:"root-label" }, "YOUR BRAIN"));
    svg.appendChild(rootGroup);

    nodes.forEach(n => {
      const p = pos[n.id];
      if (!p) return;
      const g = makeSvg("g", {
        class:"mind-node type-" + (n.type || "idea"),
        transform:"translate(" + p.x + " " + p.y + ")",
        tabindex:"0",
        role:"button",
        "aria-label":n.title
      });
      g.appendChild(makeSvg("path", { d:"M -54 0 H 54 Q 62 0 62 8 V 28 Q 62 36 54 36 H -54 Q -62 36 -62 28 V 8 Q -62 0 -54 0 Z", class:"node-card" }));
      g.appendChild(makeSvg("circle", { cx:"-45", cy:"12", r:"4", class:"node-dot" }));
      g.appendChild(makeSvg("text", { x:"-33", y:"14", class:"node-title" }, String(n.title || "Untitled").slice(0,26)));
      g.appendChild(makeSvg("text", { x:"-33", y:"28", class:"node-meta" }, (labels[n.type] || n.type || "Idea") + " · " + (n.state || "unknown")));
      g.addEventListener("click", () => inspect(n));
      g.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); inspect(n); }});
      svg.appendChild(g);
    });

    const list = $("graphNodeList");
    if (list) list.innerHTML = "";
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;" }[ch]));
  }

  function inspect(n) {
    if (!n) return;
    const box = $("nodeInspector");
    if (!box) return;
    const capital = n.capital && n.capital.amount != null
      ? (n.capital.currency || "INR") + " " + Number(n.capital.amount).toLocaleString("en-IN") + " · " + (n.capital.status || "estimated")
      : "No capital recorded";
    box.innerHTML =
      '<button class="inspector-close" aria-label="Close">×</button>' +
      '<span class="inspector-type">' + escapeHtml(labels[n.type] || n.type || "Idea") + '</span>' +
      '<h3>' + escapeHtml(n.title) + '</h3>' +
      '<p>' + escapeHtml(n.details || "No supporting context recorded yet.") + '</p>' +
      '<div><span>STATE</span><b>' + escapeHtml(n.state || "unknown") + '</b></div>' +
      '<div><span>CONFIDENCE</span><b>' + escapeHtml(n.confidence || 0) + '%</b></div>' +
      '<div><span>CAPITAL</span><b>' + escapeHtml(capital) + '</b></div>';
    box.hidden = false;
    box.querySelector(".inspector-close").onclick = () => { box.hidden = true; };
  }

  async function extract() {
    const input = $("graphInput");
    if (!input || !input.value.trim()) return;
    const provider = await FounderProvider.open();
    if (!provider) return;
    const btn = $("graphExtractBtn");
    btn.disabled = true;
    btn.innerHTML = "Mapping…";
    try {
      graph = await API.extractGraph(input.value.trim(), provider);
      render();
      input.value = "";
      App.toast("Your thinking is mapped.");
    } catch (e) {
      App.toast(e.message || "Graph extraction failed");
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Map my thinking <span>↗</span>';
    }
  }

  function init() {
    const btn = $("graphExtractBtn");
    if (btn) btn.onclick = extract;
    const refresh = $("graphRefreshBtn");
    if (refresh) refresh.onclick = load;
    render();
    load();
  }

  return { init, load, render };
})();