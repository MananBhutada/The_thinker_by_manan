"""Founder Graph extraction engine."""
import re
from typing import Any, Dict
from services.llm_service import call_openai_llm

GRAPH_PROMPT = """You are the reasoning engine for FounderOS: a living founder brain map, not a generic mind map.
A founder may dump 20 unrelated, half-formed thoughts at once. Turn that chaos into a structured graph that preserves both hierarchy and cross-connections.

CORE IDEA:
- root = the startup/company context the founder is thinking about.
- Build a visible dangling tree downward from that root.
- Branch into distinct domains only when the founder actually mentions them: money, people, product, customers, sales, marketing, operations, tax/legal, technology, fundraising, etc.
- Keep genuinely separate ideas as separate nodes. Do NOT collapse everything into one generic strategy node.
- Every node must contain its own context in details: why it exists, what the founder said about it, or what uncertainty surrounds it. Never invent missing facts.
- A child node is something that belongs under or follows from a parent.
- Two concepts can be connected without being parent/child. Represent those as separate nodes plus a semantic edge. The UI renders those cross-links as dashed lines.
- If a future plan or recommendation is explicitly discussed or strongly follows from the founder's own text, keep it as a later branch rather than mixing it into the current plan. Mark it hypothetical or unknown when appropriate.
- Blind spots, unknowns, assumptions, risks and validation questions should be separate nodes when they are concrete enough to manage.
- Preserve the founder's messiness: many things can be parallel. Do not force a single linear roadmap.

Extract only what is supported. Separate facts, assumptions, estimates, commitments and hypothetical scenarios.
Never invent amounts, dates, metrics, evidence, customers, investors or recommendations.
Return ONLY JSON:
{"root":{"title":"","summary":""},"nodes":[{"id":"n1","title":"","type":"goal|idea|initiative|problem|customer|product|market|decision|option|risk|dependency|constraint|fact|assumption|metric|experiment|unknown|investment|cost|revenue|runway","state":"known|committed|estimated|hypothetical|assumption|unknown|evidence","confidence":0,"details":"","capital":{"amount":null,"currency":"INR","status":"none|actual|committed|estimated|hypothetical"}}],"edges":[{"source":"n1","target":"n2","relationship":"depends_on|supports|conflicts_with|unlocks|alternative_to|causes|measures|tests","confidence":0}],"insights":[],"questions":[]}
GRAPH RULES:
1. Prefer 8-18 meaningful nodes over many tiny fragments.
2. Use 1-3 levels of parent/child structure where the relationship is clear.
3. Use cross-links for meaningful connections between otherwise separate branches.
4. Use depends_on when one item cannot reasonably proceed without another.
5. Use supports, causes, unlocks, measures, tests, alternative_to, conflicts_with only when justified by the input.
6. details must be useful enough that clicking a node lets the founder understand the captured context without rereading the entire brain dump.
7. Do not turn generic AI advice into a node unless the founder asked for recommendations or the idea is explicitly present.
Use at most 18 nodes and 28 edges.
Founder input:
"""
def _id(value, fallback):
    value = re.sub(r"[^a-zA-Z0-9_-]", "-", str(value or "").strip()).strip("-")
    return value[:40] or fallback

def normalize_graph(data: Dict[str, Any]) -> Dict[str, Any]:
    nodes=[]; seen=set()
    for i, raw in enumerate(data.get("nodes") or []):
        if not isinstance(raw, dict): continue
        nid=_id(raw.get("id"), "n"+str(i+1))
        if nid in seen: nid=nid+"-"+str(i+1)
        seen.add(nid)
        cap=raw.get("capital") if isinstance(raw.get("capital"),dict) else {}
        try: conf=max(0,min(100,int(raw.get("confidence") or 0)))
        except: conf=0
        nodes.append({"id":nid,"title":str(raw.get("title") or "Untitled")[:120],"type":str(raw.get("type") or "idea")[:32],"state":str(raw.get("state") or "unknown")[:24],"confidence":conf,"details":str(raw.get("details") or "")[:500],"capital":{"amount":cap.get("amount") if isinstance(cap.get("amount"),(int,float)) else None,"currency":str(cap.get("currency") or "INR")[:8],"status":str(cap.get("status") or "none")[:20]}})
    valid={n["id"] for n in nodes}; edges=[]
    for raw in data.get("edges") or []:
        if not isinstance(raw,dict): continue
        s,t=str(raw.get("source") or ""),str(raw.get("target") or "")
        if s not in valid or t not in valid or s==t: continue
        try: conf=max(0,min(100,int(raw.get("confidence") or 0)))
        except: conf=0
        edges.append({"source":s,"target":t,"relationship":str(raw.get("relationship") or "depends_on")[:32],"confidence":conf})
    root=data.get("root") if isinstance(data.get("root"),dict) else {}
    return {"root":{"title":str(root.get("title") or "Your Startup")[:120],"summary":str(root.get("summary") or "")[:300]},"nodes":nodes[:18],"edges":edges[:28],"insights":[str(x)[:300] for x in (data.get("insights") or [])[:6]],"questions":[str(x)[:300] for x in (data.get("questions") or [])[:6]]}


def merge_graph(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new founder brain dump to the living graph instead of replacing it."""
    existing = existing if isinstance(existing, dict) else {}
    incoming = incoming if isinstance(incoming, dict) else {}
    nodes = list(existing.get("nodes") or [])
    edges = list(existing.get("edges") or [])
    by_key = {str(n.get("title","")).strip().lower()+"|"+str(n.get("type","idea")).lower(): n for n in nodes}
    id_map = {}
    used_ids = {str(n.get("id")) for n in nodes}

    for raw in incoming.get("nodes") or []:
        key = str(raw.get("title","")).strip().lower()+"|"+str(raw.get("type","idea")).lower()
        if key in by_key:
            old = by_key[key]
            id_map[raw.get("id")] = old.get("id")
            new_details = str(raw.get("details") or "").strip()
            if new_details and new_details not in str(old.get("details") or ""):
                old["details"] = (str(old.get("details") or "").strip()+" "+new_details).strip()[:700]
            if raw.get("confidence") and int(raw.get("confidence") or 0) > int(old.get("confidence") or 0):
                old["confidence"] = raw.get("confidence")
            continue

        nid = str(raw.get("id") or "node")
        base = nid
        i = 2
        while nid in used_ids:
            nid = base + "-" + str(i)
            i += 1
        copy = dict(raw)
        copy["id"] = nid
        nodes.append(copy)
        used_ids.add(nid)
        by_key[key] = copy
        id_map[raw.get("id")] = nid

    edge_keys = {(e.get("source"),e.get("target"),e.get("relationship")) for e in edges}
    for e in incoming.get("edges") or []:
        s, t = id_map.get(e.get("source"), e.get("source")), id_map.get(e.get("target"), e.get("target"))
        key = (s,t,e.get("relationship"))
        if s and t and key not in edge_keys:
            edges.append({**e,"source":s,"target":t})
            edge_keys.add(key)

    insights = list(dict.fromkeys([str(x) for x in (existing.get("insights") or []) + (incoming.get("insights") or [])]))[:10]
    questions = list(dict.fromkeys([str(x) for x in (existing.get("questions") or []) + (incoming.get("questions") or [])]))[:10]
    root = existing.get("root") or incoming.get("root") or {"title":"Your Startup","summary":""}
    if not root.get("title") or root.get("title") == "Your Startup":
        root = incoming.get("root") or root

    return {"root":root,"nodes":nodes[:24],"edges":edges[:48],"insights":insights,"questions":questions}

def extract_graph(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    return normalize_graph(call_openai_llm(GRAPH_PROMPT + text[:12000], config))
