"""English text

English text HTML English text DecisionScoreEngineEnglish text 3347-3362
English textrational English text pros/cons English textEnglish text
English text benefit / risk / cost / reversibility / valueFit / confidence English text

English text 0-100 English textconfidence English text clamp English text
"""

from typing import Any, Dict, List, Optional

# English text"English text"English text
RISK_WORDS: List[str] = ["English text", "English text", "English text", "English text", "English text", "English text", "English text"]

# English text"English text"English text
REVERSIBLE_WORDS: List[str] = ["English text", "English text", "English text", "English text", "English text"]


def _clamp(low: int, high: int, value: float) -> int:
    """English text value English text [low, high] English text"""
    return max(low, min(high, round(value)))


def score(
    question: str,
    result: Optional[Dict[str, Any]],
    values: Optional[Dict[str, int]],
) -> Dict[str, int]:
    """English text

    English text
      question: English text
      result:   rational English text {pros: [...], cons: [...]}English text None
      values:   English text {efficiency, risk, growth, relationship}0-100 English text

    English text{benefit, risk, cost, reversibility, valueFit, confidence}
    """
    q = question or ""
    pros: List[str] = (result or {}).get("pros") or []
    cons: List[str] = (result or {}).get("cons") or []
    v = values or {}

    # riskEnglish text → 72English text 42
    risk = 72 if any(w in q for w in RISK_WORDS) else 42

    # reversibilityEnglish text → 72English text 46
    reversibility = 72 if any(w in q for w in REVERSIBLE_WORDS) else 46

    # benefitpros English textEnglish text → English textEnglish text 90
    benefit = min(90, 48 + len(pros) * 10 + (6 if v.get("growth", 0) > 60 else 0))

    # costcons English textEnglish text → English textEnglish text 90
    cost = min(90, 38 + len(cons) * 12 + (8 if v.get("risk", 0) > 60 else 0))

    # valueFitEnglish text + English text + (100 - risk) English text
    value_fit = round(
        (
            v.get("efficiency", 50)
            + v.get("growth", 50)
            + (100 - min(100, risk))
        )
        / 3
    )

    # confidenceEnglish textclamp English text [35, 88]
    confidence = _clamp(35, 88, (benefit + reversibility + value_fit + (100 - cost)) / 4)

    return {
        "benefit": benefit,
        "risk": risk,
        "cost": cost,
        "reversibility": reversibility,
        "valueFit": value_fit,
        "confidence": confidence,
    }


if __name__ == "__main__":
    # English textEnglish text + English text + English text
    r1 = score(
        "English text",
        {"pros": ["English text", "English text", "English text"], "cons": ["English text", "English text"]},
        {"efficiency": 70, "risk": 40, "growth": 80, "relationship": 50},
    )
    print("case1English text:", r1)
    assert r1["risk"] == 72, f"risk English text 72English text {r1['risk']}"
    assert r1["reversibility"] == 46, f"reversibility English text 46English text {r1['reversibility']}"
    # benefit = min(90, 48 + 3*10 + 6) = min(90, 84) = 84
    assert r1["benefit"] == 84, f"benefit English text 84English text {r1['benefit']}"
    # cost = min(90, 38 + 2*12 + 0) = min(90, 62) = 62risk=40 English text >60
    assert r1["cost"] == 62, f"cost English text 62English text {r1['cost']}"
    # valueFit = round((70 + 80 + (100-72)) / 3) = round(178/3) = 59
    assert r1["valueFit"] == 59, f"valueFit English text 59English text {r1['valueFit']}"
    # confidence = clamp(35, 88, round((84 + 46 + 59 + 38)/4)) = round(227/4) = 57
    assert r1["confidence"] == 57, f"confidence English text 57English text {r1['confidence']}"

    # English textEnglish text + English text
    r2 = score(
        "English text",
        {"pros": [], "cons": []},
        {"efficiency": 50, "risk": 50, "growth": 50, "relationship": 50},
    )
    print("case2English text:", r2)
    assert r2["risk"] == 42
    assert r2["reversibility"] == 72  # English text"English text"English text"English text"

    # English textNone English text
    r3 = score("", None, None)
    print("case3English text:", r3)
    assert r3["benefit"] == 48
    assert r3["cost"] == 38

    print("\nEnglish text")
