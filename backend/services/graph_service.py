"""Founder Graph engine: extraction, merging, structural upgrade and node-chat context.

The stored graph is a hybrid of three things:
  * a semantic hierarchy      -> edges with kind="structural" (root -> branch -> leaf)
  * a dependency/idea network -> edges with kind="semantic" (cross-links, dashed in the UI)
  * AI proposals              -> nodes with proposal=True linked by kind="proposal" edges
                                 (only for gaps the founder did NOT already state; never facts until accepted)
"""
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from services.llm_service import call_openai_llm

ROOT_ID = "root"
MAX_NODES = 80
MAX_EDGES = 160

NODE_TYPES = {
    "goal", "idea", "initiative", "problem", "customer", "product", "market", "decision", "option",
    "risk", "dependency", "constraint", "fact", "assumption", "metric", "experiment", "unknown",
    "investment", "cost", "revenue", "runway", "future_plan", "people", "domain", "subnode",
}
NODE_STATES = {"known", "committed", "estimated", "hypothetical", "assumption", "unknown"}
SEMANTIC_RELS = {
    "depends_on", "supports", "conflicts_with", "unlocks", "alternative_to", "causes", "measures",
    "tests", "related",
}
_LEGACY_PARENT_SOURCE = {"supports", "unlocks", "causes", "measures", "tests", "alternative_to", "conflicts_with"}

GRAPH_PROMPT = """You are the reasoning engine for FounderOS: a living map of a founder's brain, not a generic mind map.
A founder may dump 10-20 simultaneous, half-formed, partly unrelated thoughts (money, people, hiring, product, customers, sales,
marketing, tax, fundraising, runway, ideas, future plans, risks, unknowns, assumptions, experiments, decisions).
Turn that mess into a STRUCTURED graph WITHOUT flattening it into a linear roadmap.

THE GRAPH HAS THREE KINDS OF EDGES
1. structural  - "belongs under". source = "root" or a node id, target = a NEW node. Every new node (except proposals) has exactly ONE
                 structural parent. Typical shape: root -> Money / People / Product -> Runway, ROI / CTO Hire / New Product ...
2. semantic    - a cross-link between two nodes that are related but NOT parent/child (CTO Hire -- New Product, Marketing Cost -- Runway,
                 Funding -- Future Hiring). Keep both concepts as SEPARATE nodes and connect them. Never merge two concepts into one node.
3. proposal    - see BLIND SPOTS below.

NODE RULES
- root = the startup context (name, summary, the founder's stated objective). Do not make it a node.
- Only create branches the founder actually mentioned. Different topics stay different nodes.
- Each node carries its own context: "details" (what the founder said / why it exists), "summary" (<=100 chars), and when supported by
  the text: "evidence" (list of things the founder stated as fact), "assumptions" (list of things taken for granted),
  "dependencies" (list of titles this needs).
- state: known (stated as fact) | committed (decided) | estimated (rough number) | hypothetical (maybe/if) | assumption | unknown.
  Speculation ("maybe", "if we raise") MUST be hypothetical. Later plans that are not committed use type future_plan + state hypothetical.
- Never invent facts, amounts, dates, metrics, customers or investors. Leave capital.amount null unless the founder gave a number.
- type: goal|idea|initiative|problem|customer|product|market|decision|option|risk|dependency|constraint|fact|assumption|metric|experiment|unknown|investment|cost|revenue|runway|future_plan|people
- Prefer 8-18 meaningful nodes over many fragments. Use 1-3 levels of hierarchy.

BLIND SPOTS / AI PROPOSALS
- You MAY add at most 3 nodes with "proposal": true for important gaps that follow directly from the founder's text.
- CRITICAL: if the FOUNDER THEMSELVES asks a question or names an unknown (for example "what are the legal requirements...", "do I need a patent?", "how do I become compliant?"), that is FOUNDER CONTEXT and MUST be mapped as a normal node (usually unknown|decision|constraint|risk), NOT an AI proposal. Preserve the founder's question in that node's details/summary. Never label founder questions as "AI-proposed blind spots".
- A proposal is ONLY an additional question the AI introduces that the founder did not already ask or state. Do not paraphrase a founder question into a proposal.
- Each proposal needs ONE edge {kind:"proposal", relationship:"questions", source:<the node it questions>, target:<the proposal node>}.
- Proposals are suggestions, never facts. Do not create proposals for generic advice.

EXISTING GRAPH
If an EXISTING GRAPH section is given, REUSE those ids in edges instead of re-creating the same concept. Only emit NEW nodes for
 genuinely new thoughts. Existing nodes may be a structural parent (source) of new nodes or a semantic endpoint.

Return ONLY JSON:
{"root":{"title":"","summary":"","objective":""},
 "nodes":[{"id":"n1","title":"","type":"","state":"","confidence":0,"summary":"","details":"","capital":{"amount":null,"currency":"INR","status":"none|actual|committed|estimated|hypothetical"},"evidence":[],"assumptions":[],"dependencies":[],"proposal":false}],
 "edges":[{"source":"root","target":"n1","kind":"structural|semantic|proposal","relationship":"contains|depends_on|supports|conflicts_with|unlocks|alternative_to|causes|measures|tests|related|questions","confidence":0}],
 "insights":[],"questions":[]}
Use at most 18 new nodes and 30 edges.
"""


def _id(value: Any, fallback: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]", "-", str(value or "").strip()).strip("-")
    return value[:40] or fallback


def _str_list(value: Any, limit: int = 6, maxlen: int = 240) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(x).strip()[:maxlen] for x in value[:limit] if str(x or "").strip()]


def _int(value: Any, lo: int = 0, hi: int = 100) -> int:
    try:
        return max(lo, min(hi, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _empty_graph() -> Dict[str, Any]:
    return {"root": {"title": "Your Startup", "summary": "", "objective": ""}, "nodes": [], "edges": [], "insights": [], "questions": []}


def _normalize_root(raw: Any) -> Dict[str, str]:
    raw = raw if isinstance(raw, dict) else {}
    return {
        "title": str(raw.get("title") or "Your Startup")[:120],
        "summary": str(raw.get("summary") or "")[:400],
        "objective": str(raw.get("objective") or "")[:300],
    }


def _normalize_node(raw: Dict[str, Any], nid: str, created_from: str = "") -> Dict[str, Any]:
    cap = raw.get("capital") if isinstance(raw.get("capital"), dict) else {}
    ntype = str(raw.get("type") or "idea").strip().lower().replace(" ", "_")[:32]
    if ntype not in NODE_TYPES:
        ntype = "idea"
    state = str(raw.get("state") or "unknown").strip().lower()[:24]
    if state == "evidence":
        state = "known"
    if state not in NODE_STATES:
        state = "unknown"
    details = str(raw.get("details") or "")[:700]
    summary = str(raw.get("summary") or "").strip()[:160]
    if not summary and details:
        summary = re.split(r"(?<=[.!?])\s", details, maxsplit=1)[0][:140]
    proposal = bool(raw.get("proposal"))
    raw_thoughts = raw.get("thoughts") if isinstance(raw.get("thoughts"), list) else []
    thoughts = []
    for item in raw_thoughts[:40]:
        if not isinstance(item, dict):
            continue
        thoughts.append({
            "id": str(item.get("id") or "")[:80],
            "content": str(item.get("content") or "").strip()[:4000],
            "createdAt": str(item.get("createdAt") or "")[:80],
            "archived": bool(item.get("archived", False)),
            "source": str(item.get("source") or "founder")[:20],
        })
    level = str(raw.get("level") or ("domain" if ntype == "domain" else "subnode" if ntype == "subnode" else "legacy")).strip().lower()[:20]
    if level not in {"domain", "subnode", "legacy"}:
        level = "legacy"
    node = {
        "id": nid,
        "title": str(raw.get("title") or "Untitled")[:120],
        "type": ntype,
        "state": state,
        "confidence": _int(raw.get("confidence")),
        "summary": summary,
        "details": details,
        "capital": {
            "amount": cap.get("amount") if isinstance(cap.get("amount"), (int, float)) and not isinstance(cap.get("amount"), bool) else None,
            "currency": str(cap.get("currency") or "INR")[:8],
            "status": str(cap.get("status") or "none")[:20],
        },
        "evidence": _str_list(raw.get("evidence")),
        "assumptions": _str_list(raw.get("assumptions")),
        "dependencies": _str_list(raw.get("dependencies"), maxlen=120),
        "createdFrom": str(raw.get("createdFrom") or created_from)[:200],
        "proposal": proposal,
        "status": "proposed" if proposal else str(raw.get("status") or "active")[:16],
        "level": level,
        "thoughts": thoughts,
        "archived": bool(raw.get("archived", False)),
    }
    pos = raw.get("pos")
    if isinstance(pos, (list, tuple)) and len(pos) == 2 and all(isinstance(v, (int, float)) for v in pos):
        node["pos"] = [round(float(pos[0]), 1), round(float(pos[1]), 1)]
    return node


def _would_cycle(parent: Dict[str, str], child: str, new_parent: str) -> bool:
    cur: Optional[str] = new_parent
    seen: Set[str] = set()
    while cur and cur != ROOT_ID and cur not in seen:
        if cur == child:
            return True
        seen.add(cur)
        cur = parent.get(cur)
    return False


def normalize_graph(data: Dict[str, Any], existing_ids: Optional[Set[str]] = None, created_from: str = "") -> Dict[str, Any]:
    existing_ids = existing_ids or set()
    nodes: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for i, raw in enumerate(data.get("nodes") or []):
        if not isinstance(raw, dict):
            continue
        nid = _id(raw.get("id"), "n" + str(i + 1))
        if nid in seen or nid in existing_ids or nid == ROOT_ID:
            nid = nid + "-" + str(i + 1)
        seen.add(nid)
        nodes.append(_normalize_node(raw, nid, created_from))
    nodes = nodes[:18]
    new_ids = {n["id"] for n in nodes}
    proposal_ids = {n["id"] for n in nodes if n["proposal"]}
    known = new_ids | existing_ids
    edges: List[Dict[str, Any]] = []
    for raw in data.get("edges") or []:
        if not isinstance(raw, dict):
            continue
        s, t = str(raw.get("source") or ""), str(raw.get("target") or "")
        if s == t or t == ROOT_ID or t not in known or (s != ROOT_ID and s not in known):
            continue
        rel = str(raw.get("relationship") or "").strip().lower()[:32]
        kind = str(raw.get("kind") or "").strip().lower()
        if kind not in ("structural", "semantic", "proposal"):
            kind = "structural" if rel in ("contains", "child", "parent") else "semantic"
        if t in proposal_ids:
            kind, rel = "proposal", "questions"
        elif kind == "proposal":
            kind = "semantic"
        if s == ROOT_ID and kind != "structural":
            continue
        if kind == "structural":
            rel = "contains"
        elif kind == "semantic" and rel not in SEMANTIC_RELS:
            rel = "related"
        edges.append({"source": s, "target": t, "kind": kind, "relationship": rel, "confidence": _int(raw.get("confidence"))})
    return {
        "root": _normalize_root(data.get("root")),
        "nodes": nodes,
        "edges": edges[:30],
        "insights": [str(x)[:300] for x in (data.get("insights") or [])[:6]],
        "questions": [str(x)[:300] for x in (data.get("questions") or [])[:6]],
    }


def _structural_parents(edges: List[Dict[str, Any]]) -> Dict[str, str]:
    return {e["target"]: e["source"] for e in edges if e.get("kind") == "structural"}


def upgrade_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    graph = graph if isinstance(graph, dict) else {}
    out = _empty_graph()
    out["root"] = _normalize_root(graph.get("root"))
    out["insights"] = list(graph.get("insights") or [])[:10]
    out["questions"] = list(graph.get("questions") or [])[:10]
    nodes, seen = [], set()
    for i, raw in enumerate(graph.get("nodes") or []):
        if not isinstance(raw, dict):
            continue
        nid = _id(raw.get("id"), "n" + str(i + 1))
        if nid in seen or nid == ROOT_ID:
            continue
        seen.add(nid)
        nodes.append(_normalize_node(raw, nid))
    ids = {n["id"] for n in nodes}
    proposals = {n["id"] for n in nodes if n["proposal"]}
    raw_edges = [e for e in (graph.get("edges") or []) if isinstance(e, dict) and (e.get("source") in ids or e.get("source") == ROOT_ID) and e.get("target") in ids]
    has_kinds = any(e.get("kind") for e in raw_edges)
    edges: List[Dict[str, Any]] = []
    parent: Dict[str, str] = {}
    if has_kinds:
        for e in raw_edges:
            kind = e.get("kind") if e.get("kind") in ("structural", "semantic", "proposal") else "semantic"
            edges.append({"source": e["source"], "target": e["target"], "kind": kind,
                          "relationship": str(e.get("relationship") or ("contains" if kind == "structural" else "related"))[:32],
                          "confidence": _int(e.get("confidence"))})
        for e in edges:
            if e["kind"] == "structural":
                if e["target"] in parent or _would_cycle(parent, e["target"], e["source"]):
                    e["kind"], e["relationship"] = "semantic", "related"
                else:
                    parent[e["target"]] = e["source"]
    else:
        legacy_parent: Dict[str, str] = {}
        structural_pairs = set()
        for e in raw_edges:
            s, t, rel = e["source"], e["target"], e.get("relationship")
            if s == ROOT_ID or t in proposals or s in proposals or s in legacy_parent and t in legacy_parent:
                continue
            if rel == "depends_on" and s not in legacy_parent and t not in legacy_parent and not _would_cycle(legacy_parent, s, t):
                legacy_parent[s] = t; structural_pairs.add((s, t, rel))
            elif rel in _LEGACY_PARENT_SOURCE and t not in legacy_parent and s not in legacy_parent and not _would_cycle(legacy_parent, t, s):
                legacy_parent[t] = s; structural_pairs.add((s, t, rel))
        for e in raw_edges:
            key = (e["source"], e["target"], e.get("relationship"))
            if key in structural_pairs:
                child, par = (e["source"], e["target"]) if e.get("relationship") == "depends_on" else (e["target"], e["source"])
                edges.append({"source": par, "target": child, "kind": "structural", "relationship": "contains", "confidence": _int(e.get("confidence"))})
                parent[child] = par
                edges.append({"source": e["source"], "target": e["target"], "kind": "semantic", "relationship": str(e.get("relationship") or "related")[:32], "confidence": _int(e.get("confidence"))})
            else:
                edges.append({"source": e["source"], "target": e["target"], "kind": "semantic", "relationship": str(e.get("relationship") or "related")[:32], "confidence": _int(e.get("confidence"))})
    for n in nodes:
        if n["id"] not in parent and n["id"] not in proposals:
            parent[n["id"]] = ROOT_ID
            edges.append({"source": ROOT_ID, "target": n["id"], "kind": "structural", "relationship": "contains", "confidence": 0})
    out["nodes"] = nodes[:MAX_NODES]
    out["edges"] = edges[:MAX_EDGES + MAX_NODES]
    return out


def merge_graph(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new brain dump to the living graph. Never replaces existing nodes or their parents."""
    base = upgrade_graph(existing)
    incoming = incoming if isinstance(incoming, dict) else {}
    nodes: List[Dict[str, Any]] = list(base["nodes"])
    edges: List[Dict[str, Any]] = list(base["edges"])
    by_key = {n["title"].strip().lower() + "|" + n["type"]: n for n in nodes}
    by_title = {n["title"].strip().lower(): n for n in nodes}
    id_map: Dict[str, str] = {ROOT_ID: ROOT_ID, **{n["id"]: n["id"] for n in nodes}}
    used_ids = {n["id"] for n in nodes}
    new_ids: Set[str] = set()
    for raw in incoming.get("nodes") or []:
        key = str(raw.get("title", "")).strip().lower() + "|" + str(raw.get("type", "idea")).lower()
        old = by_key.get(key) or (by_title.get(str(raw.get("title", "")).strip().lower()) if not raw.get("proposal") else None)
        if old is not None:
            id_map[raw.get("id")] = old["id"]
            extra = str(raw.get("details") or "").strip()
            if extra and extra not in str(old.get("details") or ""):
                old["details"] = (str(old.get("details") or "").strip() + " " + extra).strip()[:700]
            for field in ("evidence", "assumptions", "dependencies"):
                for item in raw.get(field) or []:
                    if item not in old.get(field, []) and len(old.setdefault(field, [])) < 6:
                        old[field].append(item)
            if int(raw.get("confidence") or 0) > int(old.get("confidence") or 0):
                old["confidence"] = int(raw.get("confidence") or 0)
            continue
        nid = str(raw.get("id") or "node")
        base_id, i = nid, 2
        while nid in used_ids or nid == ROOT_ID:
            nid = base_id + "-" + str(i); i += 1
        node = dict(raw); node["id"] = nid
        nodes.append(node); used_ids.add(nid); new_ids.add(nid)
        by_key[key] = node; by_title[str(raw.get("title", "")).strip().lower()] = node; id_map[raw.get("id")] = nid
    parent = _structural_parents(edges)
    edge_keys = {(e["source"], e["target"], e["kind"], e["relationship"]) for e in edges}
    def add(s: str, t: str, kind: str, rel: str, conf: int) -> None:
        k = (s, t, kind, rel)
        if k not in edge_keys and (t, s, kind, rel) not in edge_keys:
            edges.append({"source": s, "target": t, "kind": kind, "relationship": rel, "confidence": conf}); edge_keys.add(k)
    for e in incoming.get("edges") or []:
        s, t = id_map.get(e.get("source"), e.get("source")), id_map.get(e.get("target"), e.get("target"))
        if not s or not t or s == t or t == ROOT_ID or (s != ROOT_ID and s not in used_ids) or t not in used_ids:
            continue
        kind, rel, conf = e.get("kind", "semantic"), e.get("relationship", "related"), _int(e.get("confidence"))
        if kind == "structural":
            if t in new_ids and t not in parent and not _would_cycle(parent, t, s):
                parent[t] = s; add(s, t, "structural", "contains", conf)
            elif s != ROOT_ID and parent.get(t) != s:
                add(s, t, "semantic", "related", conf)
        elif kind == "proposal":
            if t in new_ids: add(s, t, "proposal", "questions", conf)
        elif s != ROOT_ID:
            add(s, t, "semantic", rel if rel in SEMANTIC_RELS else "related", conf)
    proposal_nodes = {n["id"] for n in nodes if n.get("proposal")}
    anchored = {e["target"] for e in edges if e["kind"] == "proposal"}
    for n in list(nodes):
        if n["id"] in new_ids and n["id"] in proposal_nodes and n["id"] not in anchored:
            nodes.remove(n); continue
        if n["id"] in new_ids and n["id"] not in parent and n["id"] not in proposal_nodes:
            parent[n["id"]] = ROOT_ID; add(ROOT_ID, n["id"], "structural", "contains", 0)
    root = dict(base["root"])
    inc_root = _normalize_root(incoming.get("root")) if incoming.get("root") else {}
    for k in ("title", "summary", "objective"):
        if inc_root.get(k) and (not root.get(k) or (k == "title" and root[k] == "Your Startup")): root[k] = inc_root[k]
    insights = list(dict.fromkeys([str(x) for x in (base.get("insights") or []) + (incoming.get("insights") or [])]))[:10]
    questions = list(dict.fromkeys([str(x) for x in (base.get("questions") or []) + (incoming.get("questions") or [])]))[:10]
    kept = {n["id"] for n in nodes[:MAX_NODES]}
    edges = [e for e in edges if (e["source"] in kept or e["source"] == ROOT_ID) and e["target"] in kept][:MAX_EDGES + MAX_NODES]
    return {"root": root, "nodes": nodes[:MAX_NODES], "edges": edges, "insights": insights, "questions": questions}


def apply_proposal(graph: Dict[str, Any], node_id: str, action: str) -> Dict[str, Any]:
    g = upgrade_graph(graph)
    node = next((n for n in g["nodes"] if n["id"] == node_id and n.get("proposal")), None)
    if node is None: raise KeyError(node_id)
    if action == "reject": return remove_node(g, node_id)
    if action == "ignore": node["status"] = "ignored"; return g
    node["proposal"] = False; node["status"] = "active"
    node["state"] = "hypothetical" if node["state"] == "unknown" and node["type"] not in ("unknown",) else node["state"]
    for e in g["edges"]:
        if e["kind"] == "proposal" and e["target"] == node_id: e["kind"], e["relationship"] = "structural", "contains"
    if not any(e["kind"] == "structural" and e["target"] == node_id for e in g["edges"]):
        g["edges"].append({"source": ROOT_ID, "target": node_id, "kind": "structural", "relationship": "contains", "confidence": 0})
    return g


def remove_node(graph: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    g = upgrade_graph(graph)
    if not any(n["id"] == node_id for n in g["nodes"]): raise KeyError(node_id)
    parent = _structural_parents(g["edges"]).get(node_id, ROOT_ID)
    doomed = {node_id}
    for e in g["edges"]:
        if e["kind"] == "proposal" and e["source"] == node_id: doomed.add(e["target"])
    edges = []
    for e in g["edges"]:
        if e["kind"] == "structural" and e["source"] == node_id and e["target"] not in doomed:
            edges.append({**e, "source": parent})
        elif e["source"] in doomed or e["target"] in doomed: continue
        else: edges.append(e)
    g["nodes"] = [n for n in g["nodes"] if n["id"] not in doomed]; g["edges"] = edges
    return g


def set_positions(graph: Dict[str, Any], positions: Dict[str, Any]) -> Dict[str, Any]:
    g = upgrade_graph(graph); by_id = {n["id"]: n for n in g["nodes"]}
    for nid, pos in (positions or {}).items():
        if nid in by_id and isinstance(pos, (list, tuple)) and len(pos) == 2 and all(isinstance(v, (int, float)) for v in pos):
            by_id[nid]["pos"] = [round(max(-5000, min(5000, float(pos[0]))), 1), round(max(-5000, min(5000, float(pos[1]))), 1)]
    return g


def _existing_digest(graph: Dict[str, Any]) -> str:
    g = upgrade_graph(graph)
    if not g["nodes"]: return ""
    lines = ["EXISTING GRAPH (root: %s - %s)" % (g["root"]["title"], g["root"]["summary"][:160])]
    for n in g["nodes"][:60]: lines.append("%s | %s | %s | %s" % (n["id"], n["type"], n["state"], n["title"]))
    return "\n".join(lines) + "\n\n"


def _fallback_extract(text: str, existing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Small deterministic fallback so Map still works when the hosted model is unavailable."""
    t = " ".join(str(text or "").split())[:12000]
    low = t.lower()
    root_title = "Your Startup"
    m = re.search(r"(?:startup|company|business)\\s*(?:is|called|named)\\s+([A-Za-z0-9][A-Za-z0-9 .&_-]{1,70})", t, re.I)
    if m: root_title = m.group(1).strip(" .,-")[:80]
    specs = [
        ("money", "Money", "money"), ("runway", "Runway", "runway"),
        ("fund", "Funding", "investment"), ("raise", "Funding", "investment"),
        ("hire", "Hiring", "people"), ("cto", "CTO Hire", "people"),
        ("people", "People", "people"), ("product", "Product", "product"),
        ("build", "Product Build", "initiative"), ("customer", "Customers", "customer"),
        ("sales", "Sales", "initiative"), ("marketing", "Marketing", "initiative"),
        ("tax", "Tax", "constraint"), ("cost", "Costs", "cost"),
        ("price", "Pricing", "decision"), ("pricing", "Pricing", "decision"),
        ("risk", "Risk", "risk"), ("launch", "Launch", "initiative"),
        ("idea", "Idea", "idea"), ("future", "Future Plan", "future_plan"),
    ]
    nodes=[]; seen=set()
    def add(title, typ, details):
        key=title.lower()+"|"+typ
        if key in seen: return None
        seen.add(key); nid="fallback-"+re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-")[:28]
        if any(n["id"]==nid for n in nodes): nid += "-"+str(len(nodes)+1)
        nodes.append(_normalize_node({"id":nid,"title":title,"type":typ,"state":"known","confidence":55,"summary":details[:140],"details":details},nid,"fallback"))
        return nid
    root_children=[]
    for key,title,typ in specs:
        if key in low:
            details = t[:500] if title in ("Product","Money","People") else f"Mentioned in founder input: {t[:360]}"
            nid=add(title,typ,details)
            if nid: root_children.append(nid)
    if not nodes:
        nid=add("Founder thought", "idea", t or "No detail recorded."); root_children.append(nid)
    edges=[{"source":"root","target":nid,"kind":"structural","relationship":"contains","confidence":20} for nid in root_children]
    if "runway" in {n["title"].lower() for n in nodes} and "money" in {n["title"].lower() for n in nodes}:
        a=next(n["id"] for n in nodes if n["title"].lower()=="money"); b=next(n["id"] for n in nodes if n["title"].lower()=="runway")
        edges.append({"source":a,"target":b,"kind":"semantic","relationship":"supports","confidence":45})
    if "cto" in low and "product" in low:
        a=next((n["id"] for n in nodes if "cto" in n["title"].lower()),None); b=next((n["id"] for n in nodes if n["title"].lower()=="product"),None)
        if a and b: edges.append({"source":a,"target":b,"kind":"semantic","relationship":"supports","confidence":40})
    return {"root":{"title":root_title,"summary":t[:400],"objective":""},"nodes":nodes[:18],"edges":edges[:30],"insights":[],"questions":[]}


def _deproposalize_founder_questions(graph: Dict[str, Any], founder_text: str) -> Dict[str, Any]:
    # Prevent the model from re-labelling a founder question as an AI blind spot.
    if not founder_text or not isinstance(graph, dict): return graph
    source = " ".join(str(founder_text).lower().split())
    phrases = [p.strip() for p in re.split(r"[?.!;\\n]+", source) if len(p.strip()) >= 24]
    if not phrases: return graph
    for n in graph.get("nodes") or []:
        if not n.get("proposal"): continue
        blob = " ".join(str(n.get(k) or "").lower() for k in ("title", "summary", "details"))
        if any(p in blob or blob in p for p in phrases):
            n["proposal"] = False; n["status"] = "active"
    proposal_ids = {n["id"] for n in graph.get("nodes") or [] if n.get("proposal")}
    for e in graph.get("edges") or []:
        if e.get("kind") == "proposal" and e.get("target") not in proposal_ids:
            e["kind"] = "semantic"; e["relationship"] = "related"
    return graph

def extract_graph(text: str, config: Dict[str, Any], existing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    existing = upgrade_graph(existing) if existing else None
    prompt = GRAPH_PROMPT + "\n" + (_existing_digest(existing) if existing else "") + "Founder input:\n" + text[:12000]
    existing_ids = {n["id"] for n in existing["nodes"]} if existing else set()
    stamp = time.strftime("%Y-%m-%d") + ": " + " ".join(text.split())[:90]
    try:
        raw = call_openai_llm(prompt, config)
        raw = _deproposalize_founder_questions(raw, text)
        return normalize_graph(raw, existing_ids=existing_ids, created_from=stamp)
    except Exception as exc:
        print(f"[graph] LLM unavailable; using deterministic fallback: {type(exc).__name__}")
        return normalize_graph(_fallback_extract(text, existing=existing), existing_ids=existing_ids, created_from=stamp)


_RISKY = {"risk", "unknown", "assumption", "constraint", "problem"}


def _label(n: Dict[str, Any]) -> str:
    tag = "%s, %s" % (n.get("type", "idea"), n.get("state", "unknown"))
    if n.get("proposal"): tag += ", AI-PROPOSED (unconfirmed)"
    return "%s [%s]" % (n.get("title", "Untitled"), tag)


def _cap(n: Dict[str, Any]) -> str:
    c = n.get("capital") or {}
    if c.get("amount") is None: return "not recorded"
    return "%s %s (%s)" % (c.get("currency", "INR"), c.get("amount"), c.get("status", "estimated"))


def build_node_context(graph: Dict[str, Any], node_id: Optional[str], question: str,
                       history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[str]]:
    """Serialise the selected node and the relevant surrounding graph for the Founder Coach."""
    g = upgrade_graph(graph); by_id = {n["id"]: n for n in g["nodes"]}; root = g["root"]
    parent = _structural_parents(g["edges"]); children: Dict[str, List[str]] = {}
    for e in g["edges"]:
        if e["kind"] == "structural": children.setdefault(e["source"], []).append(e["target"])
    neighbours: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for e in g["edges"]:
        if e["kind"] in ("semantic", "proposal"):
            neighbours.setdefault(e["source"], []).append((e["target"], e)); neighbours.setdefault(e["target"], []).append((e["source"], e))
    is_root = not node_id or node_id == ROOT_ID
    if not is_root and node_id not in by_id: raise KeyError(node_id)
    sel_id = ROOT_ID if is_root else node_id; used: List[str] = [sel_id]
    out = ["FOUNDEROS GRAPH CONTEXT", "", "STARTUP:", "Name: %s" % root["title"], "Context: %s" % (root["summary"] or "not stated"),
           "Founder objective: %s" % (root.get("objective") or "not stated"), "", "SELECTED NODE:"]
    if is_root:
        out += ["Title: %s (the startup root)" % root["title"], "Details: %s" % (root["summary"] or "none recorded")]
    else:
        n = by_id[sel_id]
        out += ["Title: %s" % n["title"], "Type: %s" % n["type"], "State: %s" % n["state"],
                "Details: %s" % (n["details"] or n["summary"] or "none recorded"), "Confidence: %s%%" % n["confidence"],
                "Capital: %s" % _cap(n), "Evidence: %s" % ("; ".join(n["evidence"]) or "none recorded"),
                "Assumptions: %s" % ("; ".join(n["assumptions"]) or "none recorded"), "Dependencies: %s" % ("; ".join(n["dependencies"]) or "none recorded")]
        thoughts = [t for t in n.get("thoughts", []) if isinstance(t, dict) and not t.get("archived")]
        if thoughts:
            out += ["THOUGHT CONTENT INSIDE THIS SUB-NODE:"] + ["- %s%s" % (str(t.get("type") or "thought").upper() + ": ", str(t.get("content") or "")[:1200]) for t in thoughts[-12:]]
        if n.get("proposal"): out.append("NOTE: this node is an AI-proposed question awaiting the founder's decision, not a fact.")
    out.append(""); out.append("PARENT / STRUCTURAL CONTEXT:")
    chain, cur, guard = [], parent.get(sel_id), 0
    while cur and cur != ROOT_ID and guard < 8:
        if cur in by_id: chain.append(_label(by_id[cur])); used.append(cur)
        cur, guard = parent.get(cur), guard + 1
    out.append("Path: %s" % " > ".join([root["title"]] + list(reversed(chain)) + ([] if is_root else [by_id[sel_id]["title"]])))
    kids = [by_id[c] for c in children.get(sel_id, []) if c in by_id]; out.append("Children: %s" % ("; ".join(_label(k) for k in kids) or "none"))
    if not is_root:
        sibs = [by_id[c] for c in children.get(parent.get(sel_id, ROOT_ID), []) if c in by_id and c != sel_id]
        out.append("Siblings: %s" % ("; ".join(_label(s) for s in sibs[:6]) or "none"))
    used += [k["id"] for k in kids]; out.append(""); out.append("CONNECTED NODES / SEMANTIC RELATIONSHIPS:")
    rel_lines, linked = [], []
    for other, e in neighbours.get(sel_id, []):
        if other not in by_id: continue
        linked.append(other); arrow = "-- %s -->" % e["relationship"] if e["source"] == sel_id else "<-- %s --" % e["relationship"]
        rel_lines.append("%s %s %s" % ("This node" if not is_root else root["title"], arrow, _label(by_id[other])))
    out += rel_lines or ["none"]; used += linked; out.append("")
    near: Set[str] = set(k["id"] for k in kids) | set(linked) | ({parent[sel_id]} if sel_id in parent else set()); two_hop = set(near)
    for nid in list(near): two_hop |= set(children.get(nid, [])) | {o for o, _ in neighbours.get(nid, [])}
    two_hop.discard(sel_id); two_hop.discard(ROOT_ID)
    if is_root: two_hop = set(by_id)
    plans = [by_id[i] for i in two_hop if i in by_id and (by_id[i]["type"] == "future_plan" or by_id[i]["state"] == "hypothetical")]
    risks = [by_id[i] for i in two_hop if i in by_id and (by_id[i]["type"] in _RISKY or by_id[i].get("proposal"))]
    out.append("RELEVANT FUTURE PLANS:"); out += ["- " + _label(p) + ": " + (p["summary"] or p["details"])[:140] for p in plans[:6]] or ["none"]; out.append("")
    out.append("RELEVANT RISKS / UNKNOWNS:"); out += ["- " + _label(r) + ": " + (r["summary"] or r["details"])[:140] for r in risks[:6]] or ["none"]; used += [p["id"] for p in plans[:6]] + [r["id"] for r in risks[:6]]; out.append("")
    hist = []
    for h in (history or [])[-6:]:
        if isinstance(h, dict) and h.get("text"): hist.append("%s: %s" % ("Founder" if h.get("role") == "user" else "Coach", str(h["text"])[:500]))
    if hist: out += ["RECENT CONVERSATION ABOUT THIS NODE:"] + hist + [""]
    out += ["REASONING RULES: You are reasoning about the SELECTED NODE inside the larger founder graph above. Use the parents, connected nodes and relationships. Items marked hypothetical, assumption, estimated or AI-PROPOSED are NOT facts. Do not invent facts that are not in the graph or the question; say what is missing instead. The founder decides.", "", "FOUNDER QUESTION:", question.strip()]
    text = "\n".join(out)
    if len(text) > 7500: text = text[:7000] + "\n...[context trimmed]\n\nFOUNDER QUESTION:\n" + question.strip()[:400]
    return text, list(dict.fromkeys(used))
