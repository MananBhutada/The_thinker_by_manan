"""English text CRUD English text

- POST   /api/decision        English textEnglish text/English text
- GET    /api/decision/{id}   English text
- PATCH  /api/decision/{id}   English textexecuted/regret/dialogueHistory
- DELETE /api/decision/{id}   English text

English text SQLite English textdb.pyEnglish text _DECISIONS
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend import db
from backend.models.schemas import DecisionPatch, DecisionSave

router = APIRouter()


@router.post("/api/decision")
def save_decision(body: DecisionSave) -> Dict[str, Any]:
    """English textEnglish text id English text createdAtEnglish text dict"""
    payload = body.model_dump(exclude_none=True)
    saved = db.save_decision(payload)
    return saved


@router.get("/api/decision/{decision_id}")
def get_decision(decision_id: str) -> Dict[str, Any]:
    """English text id English textEnglish text 404"""
    dec = db.get_decision(decision_id)
    if not dec:
        raise HTTPException(status_code=404, detail="decision not found")
    return dec


@router.patch("/api/decision/{decision_id}")
def update_decision(decision_id: str, body: DecisionPatch) -> Dict[str, Any]:
    """English text executed/regret/dialogueHistoryEnglish text dict"""
    patches = body.model_dump(exclude_none=True)
    updated = db.update_decision(decision_id, patches)
    if not updated:
        raise HTTPException(status_code=404, detail="decision not found")
    return updated


@router.delete("/api/decision/{decision_id}")
def delete_decision(decision_id: str) -> Dict[str, Any]:
    """English textEnglish text 404"""
    ok = db.delete_decision(decision_id)
    if not ok:
        raise HTTPException(status_code=404, detail="decision not found")
    return {"ok": True}
