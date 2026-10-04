"""English metadata for decision modes and quick prompts."""
from typing import List, Optional
from models.schemas import ModeMeta

MODES = [
    ModeMeta(id="auto", name="Auto", icon="A", color="#317d78", description="Choose the most useful analysis mode automatically"),
    ModeMeta(id="rational", name="Reason", icon="R", color="#365385", description="Compare benefits, risks, trade-offs, and reversibility"),
    ModeMeta(id="random", name="Random", icon="?", color="#9b7636", description="Use randomness as a reflection tool for low-stakes choices"),
    ModeMeta(id="nature", name="Nature", icon="N", color="#486a55", description="Use current environmental signals as an alternative perspective"),
    ModeMeta(id="dialogue", name="Dialogue", icon="D", color="#69526f", description="Ask reflective questions that surface what you already know"),
    ModeMeta(id="fengshui", name="Traditional", icon="T", color="#b45a42", description="Explore a traditional-culture perspective for reflection only"),
]
QUICK_QUESTIONS: List[str] = [
    "Should I accept this new job?", "Should I move to another city?", "Should I keep studying or start working?",
    "Should I reach out to them?", "Should I accept this collaboration offer?",
]

def get_mode(mode_id: str) -> Optional[ModeMeta]:
    return next((m for m in MODES if m.id == mode_id), None)
