"""GET /api/modes - English text + English text"""

from typing import Any, Dict

from fastapi import APIRouter

from backend.services.modes_data import MODES, QUICK_QUESTIONS

router = APIRouter()


@router.get("/api/modes")
def get_modes() -> Dict[str, Any]:
    """English textid / English text / English text / English text / English text+ English text"""
    return {
        "modes": [m.model_dump() for m in MODES],
        "quickQuestions": QUICK_QUESTIONS,
    }
