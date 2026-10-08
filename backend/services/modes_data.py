"""Founder Coach modes."""
from typing import List, Optional
from backend.models.schemas import ModeMeta

MODES = [
    ModeMeta(id="auto", name="Auto", icon="A", color="#317d78", description="Route your startup situation to the most useful founder lens"),
    ModeMeta(id="founder", name="Founder", icon="F", color="#365385", description="Pressure-test high-stakes founder decisions and assumptions"),
    ModeMeta(id="product", name="Product", icon="P", color="#486a55", description="Challenge product bets, customer needs, roadmap and prioritization"),
    ModeMeta(id="people", name="People", icon="H", color="#69526f", description="Stress-test hiring, team, delegation and cofounder dynamics"),
    ModeMeta(id="money", name="Money", icon="$", color="#9b7636", description="Examine pricing, runway, unit economics and fundraising"),
    ModeMeta(id="growth", name="Growth", icon="G", color="#317d78", description="Pressure-test distribution, sales, retention and growth assumptions"),
    ModeMeta(id="conflict", name="Conflict", icon="C", color="#b45a42", description="Practice difficult founder and stakeholder conversations"),
]

QUICK_QUESTIONS: List[str] = [
    "Should we build this feature?",
    "Should I hire a cofounder or stay solo?",
    "Should we raise funding now or bootstrap longer?",
    "Our users like the product but nobody is paying. What are we missing?",
    "My cofounder and I disagree on the roadmap. How should I think about it?",
]

def get_mode(mode_id: str) -> Optional[ModeMeta]:
    return next((m for m in MODES if m.id == mode_id), None)
