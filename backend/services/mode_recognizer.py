"""Keyword routing for Founder Coach."""
RULES = [
    ("product", ["feature", "roadmap", "mvp", "product", "customer need", "build this", "priorit"]),
    ("people", ["hire", "hiring", "employee", "team", "cofounder", "co-founder", "delegate"]),
    ("money", ["pricing", "price", "runway", "fundrais", "investor", "revenue", "money", "valuation", "bootstrap"]),
    ("growth", ["growth", "marketing", "sales", "distribution", "retention", "acquisition", "go-to-market", "gtm"]),
    ("conflict", ["disagree", "conflict", "argument", "difficult conversation", "stakeholder", "cofounder conflict"]),
    ("founder", ["startup", "founder", "company", "launch", "pivot", "should we", "what should i do"]),
]
MODE_NAMES = {"auto":"Auto","founder":"Founder","product":"Product","people":"People","money":"Money","growth":"Growth","conflict":"Conflict"}

def explain(question: str) -> dict:
    q = (question or "").strip().lower()
    if not q:
        return {"mode":"founder","reason":"No question was provided; using Founder mode","confidence":60}
    for mode, keywords in RULES:
        for keyword in keywords:
            if keyword in q:
                return {"mode":mode,"reason":f'Matched "{keyword}"; routed to {MODE_NAMES[mode]} mode',"confidence":82}
    return {"mode":"founder","reason":"No specific startup lens matched; using Founder mode","confidence":68}

def recognize(question: str) -> str:
    return explain(question)["mode"]
