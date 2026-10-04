"""Founder Graph extraction engine."""
import re
from typing import Any, Dict
from services.llm_service import call_openai_llm

GRAPH_PROMPT = """You are the reasoning engine for FounderOS, a founder decision graph.
Turn the founder's unstructured brain dump into a semantic decision graph.
Extract only what is supported. Separate facts, assumptions, estimates, commitments and hypothetical scenarios.
Identify dependencies and sequencing where reasonably inferable. Never invent amounts, dates, metrics or evidence.
Return ONLY JSON:
{"root":{"title":"","summary":""},"nodes":[{"id":"n1","title":"","type":"goal|idea|initiative|problem|customer|product|market|decision|option|risk|dependency|constraint|fact|assumption|metric|experiment|unknown|investment|cost|revenue|runway","state":"known|committed|estimated|hypothetical|assumption|unknown|evidence","confidence":0,"details":"","capital":{"amount":null,"currency":"INR","status":"none|actual|committed|estimated|hypothetical"}}],"edges":[{"source":"n1","target":"n2","relationship":"depends_on|supports|conflicts_with|unlocks|alternative_to|causes|measures|tests","confidence":0}],"insights":[],"questions":[]}
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

def extract_graph(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    return normalize_graph(call_openai_llm(GRAPH_PROMPT + text[:12000], config))
