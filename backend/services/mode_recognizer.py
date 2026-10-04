"""English keyword-based routing for automatic decision-mode selection."""
RULES = [
    ("random", ["what should i eat","what should i watch","where should i go","which one should i pick","lunch","dinner","breakfast"]),
    ("fengshui", ["bazi","fortune","feng shui","astrology","horoscope","divination"]),
    ("rational", ["quit","job","switch career","buy a house","rent","startup","invest","loan","car","masters","study abroad"]),
    ("dialogue", ["afraid","scared","stuck","hesitant","can't let go","what should i say","should i tell"]),
    ("nature", ["relationship","love","dating","breakup","ex","marriage","emotion","travel","go outside"]),
    ("rational", ["book","clean","organize","buy","sell","switch","keep or","should i buy"]),
]
MODE_NAMES = {"auto":"Auto","rational":"Reason","random":"Random","nature":"Nature","dialogue":"Dialogue","fengshui":"Traditional"}

def explain(question: str) -> dict:
    q = (question or "").strip().lower()
    if not q: return {"mode":"auto","reason":"No question was provided","confidence":0}
    for mode, keywords in RULES:
        for keyword in keywords:
            if keyword in q:
                return {"mode":mode,"reason":f'Matched "{keyword}"; routed to {MODE_NAMES[mode]} mode',"confidence":76}
    return {"mode":"rational","reason":"No specific scenario matched; using Reason mode","confidence":52}

def recognize(question: str) -> str:
    return explain(question)["mode"]
