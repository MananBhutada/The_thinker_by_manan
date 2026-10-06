/* FounderOS graph analytics.
 * Pure functions, no DOM. Turns the founder graph into founder-language signals:
 * importance tiers, clusters, bridge nodes, structural gaps, lenses and the Founder Funnel.
 * Everything is derived from the stored graph; nothing is invented. Insights are QUESTIONS, never facts.
 */
const FounderInsights = (() => {
  const ROOT = "root";
  const MONEY_T = new Set(["runway", "cost", "revenue", "investment"]);
  const MONEY_RX = /\b(fund|funding|raise|raising|burn|pricing|price|roi|capital|invest|investor|cash|revenue|runway|budget|salary|salaries|cost|spend)/i;
  const PEOPLE_RX = /\b(hire|hiring|cto|cofounder|co-founder|team|advisor|advisors|engineer|developer|recruit|partner)/i;
  const AUDIENCE_RX = /\b(customer|customers|user|users|patient|patients|hospital|hospitals|client|clients|buyer|buyers|market)\b/i;
  const SEQ = new Set(["depends_on", "unlocks", "causes"]);
  const BUILDY = new Set(["idea", "product", "initiative", "future_plan"]);
  const PLANNY = new Set(["initiative", "product", "future_plan", "goal", "decision"]);
  const SETTLED = new Set(["known", "committed"]);

  const LENSES = [
    { id: "brain", label: "Brain", hint: "Everything, as you thought it" },
    { id: "money", label: "Money", hint: "Investment, cost, revenue, runway, funding" },
    { id: "product", label: "Product", hint: "Product, customers, market, experiments" },
    { id: "people", label: "People", hint: "Team, hiring, advisors, partners" },
    { id: "risk", label: "Risk", hint: "Risks, unknowns, assumptions, constraints" },
    { id: "evidence", label: "Evidence", hint: "Facts, metrics, experiments, anything with evidence" },
    { id: "sequence", label: "Sequence", hint: "What depends on what" },
    { id: "future", label: "Future", hint: "Future plans, ideas, goals, hypotheticals" },
  ];

  const isMoney = n => MONEY_T.has(n.type) || MONEY_RX.test(n.title || "") || (n.capital && n.capital.amount != null);
  const isPeople = n => n.type === "people" || PEOPLE_RX.test(n.title || "");
  const hasEvidence = n => (n.evidence && n.evidence.length > 0) || n.type === "fact" || n.type === "metric";

  /** Founder-owned, visible part of the graph: no pending AI proposals, no ignored nodes. */
  function live(g) {
    const nodes = ((g && g.nodes) || []).filter(n => !n.proposal && n.status !== "ignored");
    const ids = new Set(nodes.map(n => n.id));
    ids.add(ROOT);
    const edges = ((g && g.edges) || []).filter(e => e.kind !== "proposal" && ids.has(e.source) && ids.has(e.target));
    return { nodes, edges, ids };
  }

  function brandes(ids, adj) {
    const bc = {};
    ids.forEach(i => (bc[i] = 0));
    ids.forEach(s => {
      const stack = [], pred = {}, sigma = {}, dist = {}, delta = {};
      ids.forEach(v => { pred[v] = []; sigma[v] = 0; dist[v] = -1; delta[v] = 0; });
      sigma[s] = 1; dist[s] = 0;
      const q = [s];
      for (let h = 0; h < q.length; h++) {
        const v = q[h];
        stack.push(v);
        (adj[v] || []).forEach(w => {
          if (dist[w] < 0) { dist[w] = dist[v] + 1; q.push(w); }
          if (dist[w] === dist[v] + 1) { sigma[w] += sigma[v]; pred[w].push(v); }
        });
      }
      while (stack.length) {
        const w = stack.pop();
        pred[w].forEach(v => { delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w]); });
        if (w !== s) bc[w] += delta[w];
      }
    });
    ids.forEach(i => (bc[i] /= 2));
    return bc;
  }

  function analyze(g) {
    const { nodes, edges } = live(g);
    const byId = new Map(nodes.map(n => [n.id, n]));
    const title = id => (id === ROOT ? (g.root && g.root.title) || "Your startup" : (byId.get(id) || {}).title || id);

    // structural parent -> cluster = the branch directly under root
    const parent = {}, kids = {};
    edges.forEach(e => {
      if (e.kind === "structural" && !parent[e.target]) {
        parent[e.target] = e.source;
        (kids[e.source] = kids[e.source] || []).push(e.target);
      }
    });
    const branchOf = id => {
      let c = id, guard = 0;
      while (parent[c] && parent[c] !== ROOT && guard++ < 20) c = parent[c];
      return c;
    };
    const cluster = {};
    nodes.forEach(n => (cluster[n.id] = branchOf(n.id)));

    // adjacency without the root: bridges must come from real structure and cross-links
    const adj = {}, deg = {};
    nodes.forEach(n => { adj[n.id] = []; deg[n.id] = 0; });
    const rootDeg = {};
    edges.forEach(e => {
      if (e.source === ROOT || e.target === ROOT) { rootDeg[e.source === ROOT ? e.target : e.source] = 1; return; }
      if (!adj[e.source] || !adj[e.target]) return;
      adj[e.source].push(e.target); adj[e.target].push(e.source);
      deg[e.source]++; deg[e.target]++;
    });
    const ids = nodes.map(n => n.id);
    const bc = ids.length <= 160 ? brandes(ids, adj) : {};
    const maxBc = Math.max(1e-9, ...ids.map(i => bc[i] || 0));
    const betweenness = {}, importance = {};
    ids.forEach(i => {
      betweenness[i] = (bc[i] || 0) / maxBc;
      importance[i] = deg[i] + (rootDeg[i] ? 1 : 0) + 4 * betweenness[i];
    });

    const scores = ids.map(i => importance[i]).sort((a, b) => a - b);
    const p85 = scores.length ? scores[Math.min(scores.length - 1, Math.floor(scores.length * 0.85))] : 0;
    const tier = {};
    ids.forEach(i => {
      const childCount = (kids[i] || []).length;
      const isBranch = parent[i] === ROOT || !parent[i];
      if ((isBranch && childCount >= 2) || (importance[i] >= p85 && importance[i] >= 4)) tier[i] = "core";
      else if (deg[i] === 0 || (deg[i] <= 1 && !childCount)) tier[i] = "peripheral";
      else tier[i] = "support";
    });

    // clusters
    const cmap = {};
    nodes.forEach(n => { const c = cluster[n.id]; (cmap[c] = cmap[c] || []).push(n.id); });
    const clusters = Object.keys(cmap).map(c => ({ id: c, title: title(c), ids: cmap[c], size: cmap[c].length }))
      .sort((a, b) => b.size - a.size);

    // bridge nodes: neighbours (any edge kind) spanning 2+ clusters other than their own
    const bridges = {};
    ids.forEach(i => {
      const span = new Set([cluster[i]]);
      adj[i].forEach(j => span.add(cluster[j]));
      if (span.size >= 3 || (span.size === 2 && betweenness[i] >= 0.6 && adj[i].some(j => cluster[j] !== cluster[i])))
        bridges[i] = [...span].map(title);
    });

    const crossLinks = edges.filter(e => e.kind === "semantic").length;
    const covered = nodes.filter(hasEvidence).length;
    return {
      degree: deg, betweenness, importance, tier, cluster, clusters, bridges, title,
      loose: nodes.filter(n => deg[n.id] === 0).map(n => n.id),
      stats: { nodes: nodes.length, crossLinks, evidenceCoverage: nodes.length ? covered / nodes.length : 0, evidenceCount: covered },
    };
  }

  /** Graph-derived questions. Always phrased as questions; AI never turns them into facts. */
  function insights(g) {
    const { nodes, edges } = live(g);
    if (nodes.length < 2) return [];
    const A = analyze(g);
    const byId = new Map(nodes.map(n => [n.id, n]));
    const t = id => A.title(id);
    const nb = {};
    nodes.forEach(n => (nb[n.id] = new Set()));
    edges.forEach(e => {
      if (e.source !== ROOT && e.target !== ROOT && nb[e.source] && nb[e.target]) { nb[e.source].add(e.target); nb[e.target].add(e.source); }
    });
    const within2 = id => { const s = new Set([id]); nb[id].forEach(j => { s.add(j); nb[j].forEach(k => s.add(k)); }); return s; };
    const out = [];
    const push = (kind, label, title, body, ids, severity, ask) => out.push({ id: kind + ":" + ids.join(","), kind, label, title, body, ids, severity, ask });
    const moneyNodes = nodes.filter(isMoney);

    // 1. money blind spots
    if (nodes.length >= 5 && !moneyNodes.length) {
      push("money-missing", "Money blind spot", "Nothing on your map is about money",
        "No cost, runway, funding or revenue node exists yet. Is that deliberate, or just not said out loud yet?", [], 2,
        "What financial facts about my startup am I not tracking?");
    } else {
      const cands = nodes.filter(n => isPeople(n) && !isMoney(n) && ![...within2(n.id)].some(i => byId.get(i) && isMoney(byId.get(i))));
      const candIds = new Set(cands.map(n => n.id));
      // report the specific leaf (CTO Hire), not also its parent branch (People)
      cands.filter(n => !edges.some(e => e.kind === "structural" && e.source === n.id && candIds.has(e.target))).forEach(n => {
        {
          push("money-gap", "Money blind spot", t(n.id) + " has no financial link",
            t(n.id) + " is connected to " + ([...nb[n.id]].slice(0, 3).map(t).join(", ") || "the rest of your map") + " but not to anything financial (runway, cost, funding). Is the financial impact already considered?",
            [n.id], 3, "What would " + t(n.id) + " cost me, and how does that change my runway?");
        }
      });
    }

    // 2. structural gaps between clusters
    const big = A.clusters.filter(c => c.size >= 2);
    const gaps = [];
    for (let i = 0; i < big.length; i++) for (let j = i + 1; j < big.length; j++) {
      const a = new Set(big[i].ids), b = new Set(big[j].ids);
      const linked = edges.some(e => e.kind !== "structural" && ((a.has(e.source) && b.has(e.target)) || (b.has(e.source) && a.has(e.target))));
      if (!linked) gaps.push({ a: big[i], b: big[j], w: big[i].size * big[j].size });
    }
    gaps.sort((x, y) => y.w - x.w).slice(0, 2).forEach(gp => {
      push("gap", "Structural gap", gp.a.title + " and " + gp.b.title + " are not connected",
        gp.a.title + " (" + gp.a.size + " thoughts) and " + gp.b.title + " (" + gp.b.size + ") share no links. Is there a dependency between them that you haven't drawn?",
        [gp.a.id, gp.b.id], 2, "Is there a dependency between " + gp.a.title + " and " + gp.b.title + " that I'm missing?");
    });

    // 3. orphaned ideas
    nodes.filter(n => BUILDY.has(n.type) && !isMoney(n) && !isPeople(n)).forEach(n => {
      const near = within2(n.id);
      const hasAudience = [...near].some(i => { const m = byId.get(i); return m && i !== n.id && (m.type === "customer" || m.type === "market" || AUDIENCE_RX.test(m.title || "")); });
      if (!hasAudience && out.filter(o => o.kind === "orphan").length < 2)
        push("orphan", "Orphaned idea", t(n.id) + " has no customer attached",
          t(n.id) + " isn't linked to any customer or market on your map. Who is this actually for?", [n.id], 2, "Who is " + t(n.id) + " actually for?");
    });

    // 4. overloaded nodes
    nodes.forEach(n => {
      const d = A.degree[n.id];
      if (d >= 6) push("overload", "Overloaded node", t(n.id) + " touches " + d + " other things",
        "Unusually high downstream impact: " + [...nb[n.id]].slice(0, 4).map(t).join(", ") + (d > 4 ? " and more" : "") + ". A change here ripples widely.", [n.id, ...nb[n.id]], 2,
        "What changes everywhere else if I get " + t(n.id) + " wrong?");
    });

    // 5. unresolved dependencies
    const dep = [];
    edges.forEach(e => {
      if (e.relationship === "depends_on") dep.push([e.source, e.target]);
      else if (e.relationship === "unlocks") dep.push([e.target, e.source]);
    });
    dep.forEach(([needy, needed]) => {
      const a = byId.get(needy), b = byId.get(needed);
      if (a && b && PLANNY.has(a.type) && !SETTLED.has(b.state) && (["decision", "option", "unknown", "assumption", "dependency", "risk"].includes(b.type) || b.state === "unknown"))
        push("dependency", "Unresolved dependency", t(needy) + " waits on " + t(needed),
          t(needy) + " depends on " + t(needed) + ", which is still " + (b.state || "open") + ". Until that settles, the chain stays shaky.", [needy, needed], 3,
          "What has to be decided about " + t(needed) + " before " + t(needy) + " can move?");
    });

    // 6. high-risk assumptions: a plan resting on unvalidated assumptions / unknowns
    nodes.filter(n => PLANNY.has(n.type)).forEach(n => {
      const shaky = [...nb[n.id]].map(i => byId.get(i)).filter(m => m && (m.type === "assumption" || m.type === "unknown" || m.state === "assumption" || m.state === "unknown") && !hasEvidence(m));
      const own = (n.assumptions || []).length && !(n.evidence || []).length;
      if (shaky.length) push("assumption", "Untested assumption", t(n.id) + " rests on " + shaky.map(m => m.title).slice(0, 2).join(" and "),
        t(n.id) + " is linked to " + shaky.length + " unvalidated " + (shaky.length === 1 ? "assumption or unknown" : "assumptions or unknowns") + " with no evidence recorded. What would you need to see to trust it?",
        [n.id, ...shaky.map(m => m.id)], 3, "What is the cheapest way to validate what " + t(n.id) + " depends on?");
      else if (own) push("assumption", "Untested assumption", t(n.id) + " lists " + n.assumptions.length + " assumption" + (n.assumptions.length === 1 ? "" : "s") + " and no evidence",
        "You've named what you're taking for granted around " + t(n.id) + ", but nothing is recorded as evidence yet.", [n.id], 2, "Which assumption behind " + t(n.id) + " is most likely to be wrong?");
    });

    // 7. loose thoughts (periphery) and bridge node
    if (A.loose.length) push("periphery", "Periphery", A.loose.length + " loose " + (A.loose.length === 1 ? "thought" : "thoughts") + " at the edge",
      A.loose.slice(0, 4).map(t).join(", ") + " " + (A.loose.length === 1 ? "isn't" : "aren't") + " connected to anything. One of these may matter more than it looks.", A.loose, 1,
      "Which of my loose thoughts might actually be important?");
    const bridgeIds = Object.keys(A.bridges).sort((x, y) => A.importance[y] - A.importance[x]);
    if (bridgeIds.length) {
      const id = bridgeIds[0];
      push("bridge", "Bridge node", t(id) + " connects " + A.bridges[id].slice(0, 3).join(", "),
        "Several parts of your thinking pass through " + t(id) + ". It's a hinge: moving it moves them.", [id], 1, "Why does " + t(id) + " connect so many parts of my startup?");
    }
    return out.sort((x, y) => y.severity - x.severity).slice(0, 12);
  }

  /** Lens -> Set of node ids to emphasise (null = no lens). */
  function lensIds(g, lens) {
    if (!lens || lens === "brain") return null;
    const nodes = (g && g.nodes) || [];
    const set = new Set();
    const test = {
      money: n => isMoney(n),
      product: n => ["product", "customer", "market", "experiment", "problem", "idea", "initiative"].includes(n.type),
      people: n => isPeople(n) || n.type === "customer",
      risk: n => ["risk", "unknown", "dependency", "constraint", "assumption"].includes(n.type) || n.state === "assumption" || n.state === "unknown" || n.proposal,
      evidence: n => hasEvidence(n) || n.type === "experiment",
      future: n => ["future_plan", "idea", "goal"].includes(n.type) || n.state === "hypothetical",
    }[lens];
    if (lens === "sequence") {
      ((g && g.edges) || []).forEach(e => { if (SEQ.has(e.relationship)) { set.add(e.source); set.add(e.target); } });
      return set;
    }
    if (test) nodes.forEach(n => { if (test(n)) set.add(n.id); });
    return set;
  }

  /** Funnel: each founder-owned node is classified once. AI proposals are counted separately, never as facts. */
  const STAGES = [
    { id: "thought", label: "Thought", blurb: "Said, but not yet questioned" },
    { id: "question", label: "Question", blurb: "Unknowns you haven't answered" },
    { id: "assumption", label: "Assumption", blurb: "Taken for granted or hypothetical" },
    { id: "evidence", label: "Evidence", blurb: "Facts, metrics, things with proof" },
    { id: "experiment", label: "Experiment", blurb: "Tests you've set up" },
    { id: "decision", label: "Decision", blurb: "Choices still on the table" },
    { id: "commitment", label: "Commitment", blurb: "Things you've committed to" },
  ];
  function stageOf(n) {
    if (n.state === "committed") return "commitment";
    if (n.type === "experiment") return "experiment";
    if (n.type === "decision" || n.type === "option") return "decision";
    if (n.type === "fact" || n.type === "metric" || (n.evidence && n.evidence.length && SETTLED.has(n.state))) return "evidence";
    if (n.type === "assumption" || n.state === "assumption" || n.state === "hypothetical") return "assumption";
    if (n.type === "unknown" || n.state === "unknown") return "question";
    return "thought";
  }
  function funnel(g) {
    const { nodes } = live(g);
    const buckets = {};
    STAGES.forEach(s => (buckets[s.id] = []));
    nodes.forEach(n => buckets[stageOf(n)].push(n.id));
    const pending = ((g && g.nodes) || []).filter(n => n.proposal && n.status !== "ignored").length;
    return { total: nodes.length, pendingProposals: pending, stages: STAGES.map(s => Object.assign({}, s, { ids: buckets[s.id], count: buckets[s.id].length })) };
  }

  const api = { analyze, insights, lensIds, funnel, LENSES, SEQ, stageOf, isMoney, isPeople };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  return api;
})();