"""English prompts for BlindSpot AI decision analysis."""
from typing import Any, Dict

def _base(instruction: str, question: str) -> str:
    return f"""You are BlindSpot AI, a decision-support assistant. Do not make the decision for the user. Surface assumptions, overlooked factors, conflicts, uncertainty, missing information, and useful reflection questions. Be concrete, concise, and conversational. Return valid JSON only.\n\nQuestion: {question}\n\n{instruction}"""

def rational(question: str, values: Dict[str, int]) -> str:
    return _base('Analyze benefits, risks, opportunity costs, reversibility, value conflicts, and second-order effects. Return {"type":"rational","pros":[...],"cons":[...],"conclusion":"a neutral synthesis, not a recommendation"}.', question)

def random(question: str) -> str:
    return _base('Treat randomness only as a reflection device. Return exactly six concrete options in {"type":"random","options":[...]}. Do not present the random result as evidence.', question)

def nature(question: str, weather_ctx: Dict[str, Any]) -> str:
    return _base(f'Use the following environmental context only as an alternative perspective: {weather_ctx}. Return {"type":"nature","time":"...","season":"...","weather":"...","sun":"...","wind":"...","source":"...","isReal":true/false,"signal":"...","poem":"...","suggestion":"..."}.', question)

def dialogue(question: str) -> str:
    return _base('Ask one high-value reflective question and provide three possible responses. Return {"type":"dialogue","question":"...","options":["...","...","..."]}.', question)

def fengshui(question: str, bazi: Any = None) -> str:
    return _base(f'Provide a clearly labeled traditional-culture perspective only, never a factual prediction. Birth information/context: {bazi}. Return {"type":"fengshui","needBirth":true/false,"question":"...","bazi":"...","wuxing":"...","element":"...","analysis":"...","suggestion":"..."}.', question)
