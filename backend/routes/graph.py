"""Founder Graph API.

Extraction and node chat share one request-scoped provider resolver. BYOK values
are accepted only for the current request and are never written to graph state.
"""
import os
from fastapi import APIRouter, HTTPException

import db
from models.graph_schemas import (
    GraphChatRequest,
    GraphExtractRequest,
    GraphPositionsRequest,
    GraphProposalRequest,
)
from services.graph_service import (
    apply_proposal,
    build_node_context,
    extract_graph,
    merge_graph,
    remove_node,
    set_positions,
    upgrade_graph,
)
import services.llm_service as _llm_service
from services.llm_service import NoApiKeyError, call_llm

_llm_service._LLM_TIMEOUT = min(max(getattr(_llm_service, "_LLM_TIMEOUT", 20.0), 8.0), 25.0)

router = APIRouter()


def _config(req):
    if req.provider == "free":
        # Free mode may run without a hosted key. The graph service has a
        # deterministic extraction fallback, so the workspace remains usable
        # when the deployment has no AI secret configured.
        from config import get_effective_config
        stored = get_effective_config()
        key = os.environ.get("FOUNDEROS_FREE_AI_API_KEY", "") or stored.get("llm_api_key", "")
        return {
            "llm_api_key": key,
            "llm_model": (os.environ.get("FOUNDEROS_FREE_AI_MODEL", "").strip() or stored.get("llm_model", "").strip() or "nvidia/nemotron-3.5-super:free"),
            "llm_base_url": os.environ.get("FOUNDEROS_FREE_AI_BASE_URL", "") or stored.get("llm_base_url", "") or "https://openrouter.ai/api/v1",
            "llm_fallback_models": os.environ.get(
                "FOUNDEROS_FREE_AI_FALLBACK_MODELS",
                "openrouter/free",
            ),
        }
    if not req.apiKey or not req.llmModel or not req.llmBaseUrl:
        raise HTTPException(status_code=402, detail="Add your API key, model and base URL for this session.")
    return {"llm_api_key": req.apiKey, "llm_model": req.llmModel, "llm_base_url": req.llmBaseUrl}


@router.post("/api/graph/extract")
def extract(req: GraphExtractRequest):
    config = _config(req)
    try:
        current = db.get_graph()
        incoming = extract_graph(req.text, config, existing=current)
        graph = merge_graph(current, incoming)
        db.save_graph(graph)
        return graph
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:500])


@router.get("/api/graph")
def get_graph():
    return upgrade_graph(db.get_graph())


@router.post("/api/graph/mutate")
def mutate_graph(payload: dict):
    """Persist a founder-authorized graph mutation from the interactive workspace."""
    graph = payload.get("graph")
    if not isinstance(graph, dict):
        raise HTTPException(status_code=400, detail="graph is required")
    graph.setdefault("root", {"title": "Your startup"})
    graph.setdefault("nodes", [])
    graph.setdefault("edges", [])
    graph.setdefault("insights", [])
    graph.setdefault("questions", [])
    db.save_graph(graph)
    return upgrade_graph(graph)


@router.post("/api/graph/chat")
def chat_about_node(req: GraphChatRequest):
    """Reason about a graph node and persist the full conversation."""
    config = _config(req)
    graph = db.get_graph()
    context_node_id = req.nodeId or "root"
    session = db.get_or_create_chat_session(
        req.sessionId,
        context_node_id,
        title="Founder Coach",
    )
    prior = db.list_chat_messages(session["sessionId"], limit=40)
    history = req.history if not prior else [
        {"role": "user" if m["role"] == "user" else "coach", "text": m["content"]}
        for m in prior[-12:]
    ]
    try:
        context, used = build_node_context(
            graph,
            req.nodeId,
            req.question,
            history,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="That node no longer exists in the graph.")
    db.save_chat_message(session["sessionId"], "user", req.question, {"nodeId": context_node_id})

    try:
        result = call_llm(context, req.mode, config, language="en", allow_mock=False)
    except NoApiKeyError:
        result = {
            "type": "fallback",
            "summary": "Coach fallback: start from the selected thought and inspect its connected assumptions, dependencies, risks and evidence before deciding.",
            "confidence": 0,
            "perspectives": ["Founder-created information remains authoritative.", "Unverified AI or hypothetical reasoning should stay explicitly uncertain."],
            "nextSteps": ["Add the missing assumption as a branch.", "Connect this thought to the decision, risk or customer evidence it depends on."],
            "risks": ["No hosted LLM key is configured for this request."],
            "_source": "fallback"
        }
    except Exception:
        result = {
            "type": "auto",
            "summary": "The hosted coach is temporarily unavailable. I can still help you reason from the graph once the model responds.",
            "confidence": 0,
            "perspectives": [
                "The selected node should be considered together with its parent and connected nodes.",
                "Any estimated, hypothetical or assumed information should stay explicitly uncertain.",
            ],
            "nextSteps": ["Try the question again in a moment.", "Validate the most important unknown before committing resources."],
            "risks": ["AI reasoning is unavailable for this request; do not treat this fallback as a recommendation."],
            "_source": "fallback",
        }

    from routes.chat import _try_build_brief
    brief = _try_build_brief(result, mode=req.mode)
    summary = result.get("summary") or result.get("conclusion") or ""
    assistant_text = summary or "No response."
    db.save_chat_message(
        session["sessionId"],
        "assistant",
        assistant_text,
        {"mode": req.mode, "nodeId": context_node_id, "result": result},
    )
    return {
        "mode": req.mode,
        "nodeId": context_node_id,
        "sessionId": session["sessionId"],
        "reply": assistant_text,
        "brief": brief.model_dump() if brief else None,
        "result": result,
        "contextNodes": used,
    }


@router.get("/api/graph/chat/sessions")
def list_chat_sessions(nodeId: str | None = None):
    """List persisted coach conversations for this workspace."""
    return {"sessions": db.list_chat_sessions(nodeId, limit=50)}


@router.get("/api/graph/chat/{session_id}")
def get_chat_history(session_id: str):
    """Return one persisted coach conversation."""
    sessions = db.list_chat_sessions(limit=100)
    if not any(s["sessionId"] == session_id for s in sessions):
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return {"session": next(s for s in sessions if s["sessionId"] == session_id), "messages": db.list_chat_messages(session_id)}


@router.post("/api/graph/proposal")
def resolve_proposal(req: GraphProposalRequest):
    try:
        graph = apply_proposal(db.get_graph(), req.nodeId, req.action)
    except KeyError:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    db.save_graph(graph)
    return graph


@router.delete("/api/graph/node/{node_id}")
def delete_node(node_id: str):
    try:
        graph = remove_node(db.get_graph(), node_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Node not found.")
    db.save_graph(graph)
    return graph


@router.post("/api/graph/positions")
def save_positions(req: GraphPositionsRequest):
    graph = set_positions(db.get_graph(), req.positions)
    db.save_graph(graph)
    return {"ok": True}
