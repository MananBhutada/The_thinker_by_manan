"""Founder Graph API."""
import os
from fastapi import APIRouter, HTTPException
import db
from models.graph_schemas import GraphExtractRequest
from services.graph_service import extract_graph

router=APIRouter()

def _config(req):
    if req.provider=="free":
        key=os.environ.get("FOUNDEROS_FREE_AI_API_KEY","")
        if not key:
            raise HTTPException(status_code=503, detail="FounderOS Free AI is not configured on this deployment yet.")
        return {"llm_api_key":key,"llm_model":os.environ.get("FOUNDEROS_FREE_AI_MODEL","qwen/qwen3.8-27b:free"),"llm_base_url":os.environ.get("FOUNDEROS_FREE_AI_BASE_URL","https://openrouter.ai/api/v1")}
    if not req.apiKey or not req.llmModel or not req.llmBaseUrl:
        raise HTTPException(status_code=402, detail="Add your API key, model and base URL for this session.")
    return {"llm_api_key":req.apiKey,"llm_model":req.llmModel,"llm_base_url":req.llmBaseUrl}

@router.post("/api/graph/extract")
def extract(req: GraphExtractRequest):
    try:
        graph=extract_graph(req.text,_config(req))
        db.save_graph(graph)
        return graph
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:500])

@router.get("/api/graph")
def get_graph():
    return db.get_graph()
