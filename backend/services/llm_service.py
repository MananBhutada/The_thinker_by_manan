"""LLM English text

English text
  - English textconfig English text llm_api_key + llm_base_url + llm_model English text
    English text httpx English text OpenAI English text/chat/completions
  - mock English textEnglish text ModeResultEnglish text _source='mock'

6 English text
  - auto: English textBrief English text
  - rational: English text + English text
  - random: 6 English textEnglish textEnglish text/English text/English text
  - nature: English text nature_serviceEnglish text
  - dialogue: English text + 3 English text
  - fengshui: English text bazi_engine.analyzeEnglish text needBirth=true

English textAPI Key English text
"""

import json
import re
from typing import Any, Dict, Optional

import httpx

from backend.config import get_effective_config, has_llm_config
from backend.models.schemas import Brief

_LLM_TIMEOUT = 20.0

# English text Brief mock English textgenerate_brief English text
_HUMANIZE = (
    "English textEnglish textEnglish textAIEnglish text"
    "English text\"English text/English text/English text/English text\"English textEnglish text"
    "English textEnglish textEnglish text"
)

# random mock English textEnglish text
_RANDOM_POOLS = {
    "zh-CN": {
        "eat": ["English text", "English text", "English text", "English text", "English text", "English text"],
        "watch": ["English text", "English text", "English text", "English text", "English text", "English text"],
        "buy": ["English text", "English text", "English text", "English text", "English text", "English text"],
        "default": ["English text", "English text", "English text", "English text", "English text", "English text"],
    },
    "en": {
        "eat": ["Malatang", "Sushi", "Salad", "Lanzhou noodles", "Braised chicken", "Jianbing"],
        "watch": ["Action movie", "Documentary", "Comedy", "Thriller", "Animation", "Variety show"],
        "buy": ["Wait 3 days", "Find a cheaper alternative", "Buy second-hand", "Wait for sale", "Just buy it", "Skip it"],
        "default": ["Try this first", "Think differently", "Sleep on it", "Ask a friend", "Take a small step", "Flip a coin"],
    },
}
# random English text 6 English text
_RANDOM_FALLBACK = {
    "zh-CN": ["English text", "English text", "English text", "English text", "English text", "English text"],
    "en": ["Pause", "Change angle", "Ask a friend", "Decide tomorrow", "Take a tiny step", "Keep the status quo"],
}

# dialogue English text 3 English text
_DIALOGUE_FALLBACK = {
    "zh-CN": ["English text", "English text", "English text"],
    "en": ["Fear of loss", "Want change", "Need more info"],
}


def _build_endpoint(base_url: str) -> str:
    """English text base_url English text chat completions English text

    English textEnglish text endpointEnglish text /chat/completionsEnglish text baseEnglish text .../v1
    """
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/"):
        return base_url + "chat/completions"
    return base_url.rstrip("/") + "/chat/completions"


def _parse_json_content(text: str) -> Any:
    """English text LLM English text JSONEnglish text ```json English text"""
    if not text:
        return None
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            cleaned = m.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _response_text(data: Dict[str, Any]) -> str:
    """Extract text from a Responses API JSON payload."""
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    chunks = []
    for item in data.get("output") or []:
        for part in item.get("content") or []:
            if isinstance(part, dict) and part.get("type") in ("output_text", "text"):
                value = part.get("text")
                if isinstance(value, str):
                    chunks.append(value)
    return "\n".join(chunks).strip()


def _raise_llm_error(resp: httpx.Response) -> None:
    detail = ""
    try:
        payload = resp.json()
        err = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(err, dict):
            detail = err.get("message") or err.get("code") or ""
        elif isinstance(payload, dict):
            detail = payload.get("message") or ""
    except Exception:
        pass
    detail = str(detail).strip()[:400]
    raise RuntimeError(f"LLM request failed ({resp.status_code}){': ' + detail if detail else ''}")


def _candidate_models(config: Dict[str, Any]) -> list[str]:
    """Return the primary model followed by optional provider fallbacks."""
    primary = str(config.get("llm_model") or "").strip()
    raw_fallbacks = config.get("llm_fallback_models") or []
    if isinstance(raw_fallbacks, str):
        raw_fallbacks = [item.strip() for item in raw_fallbacks.split(",")]
    candidates = []
    for model in [primary, *list(raw_fallbacks)]:
        model = str(model or "").strip()
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def call_openai_llm(prompt: str, config: Dict[str, Any], image: Optional[str] = None) -> Dict[str, Any]:
    """Call OpenAI or an OpenAI-compatible provider, with optional model failover."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['llm_api_key']}",
    }
    base = config["llm_base_url"].rstrip("/")
    is_openai = "api.openai.com" in base
    models = _candidate_models(config)
    if not models:
        raise RuntimeError("No LLM model is configured")

    if image and isinstance(image, str) and image.startswith("data:"):
        if is_openai:
            user_content = [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": image},
            ]
        else:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image}},
            ]
    else:
        user_content = prompt

    retryable_statuses = {402, 404, 408, 429, 500, 502, 503, 504}
    last_error: Optional[Exception] = None

    for index, model in enumerate(models):
        if is_openai:
            body = {
                "model": model,
                "input": [{"role": "user", "content": user_content if isinstance(user_content, list) else [
                    {"type": "input_text", "text": user_content}
                ]}],
            }
            url = base + "/responses"
        else:
            body = {
                "model": model,
                "messages": [{"role": "user", "content": user_content}],
                "temperature": 0.2,
            }
            url = _build_endpoint(base)

        try:
            with httpx.Client(timeout=_LLM_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=body)
        except httpx.RequestError as exc:
            last_error = RuntimeError(f"Could not reach the LLM provider: {exc}")
            if index < len(models) - 1:
                print(f"[llm] model={model} request failed; trying fallback")
                continue
            raise last_error from exc

        if not resp.is_success:
            try:
                _raise_llm_error(resp)
            except RuntimeError as exc:
                last_error = exc
                if resp.status_code in retryable_statuses and index < len(models) - 1:
                    print(f"[llm] model={model} returned {resp.status_code}; trying fallback")
                    continue
                raise

        try:
            data = resp.json()
        except ValueError as exc:
            last_error = RuntimeError("LLM provider returned invalid JSON")
            if index < len(models) - 1:
                print(f"[llm] model={model} returned invalid JSON; trying fallback")
                continue
            raise last_error from exc

        content = _response_text(data) if is_openai else (
            (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        )
        parsed = _parse_json_content(content)
        if isinstance(parsed, dict):
            return parsed

        last_error = RuntimeError("LLM returned text instead of the required JSON structure")
        if index < len(models) - 1:
            print(f"[llm] model={model} returned non-JSON output; trying fallback")
            continue
        raise last_error

    raise last_error or RuntimeError("LLM request failed")

# ─── Brief English textEnglish text API──────────────────────────────────────


def _build_brief_prompt(question: str, mode: str, has_image: bool = False) -> str:
    image_hint = "\n\nEnglish textEnglish text" if has_image else ""
    return (
        f"{_HUMANIZE}\n\n"
        f"English textEnglish text\"{question}\"English text{mode}English text"
        f"{image_hint}"
        "English text JSON\n"
        '{"summary":"English text","confidence":0-100English text,'
        '"perspectives":["English text1","English text2","English text3"],"nextSteps":["English text1","English text2"],'
        '"risks":["English text1","English text2"]}'
    )


# English text Brief mock English textsummary English text {question}/{mode} English text
_MOCK_BRIEFS_I18N: Dict[str, Dict[str, Dict[str, Any]]] = {
    "auto": {
        "zh-CN": {
            "summary": "English text{question}English text{mode}English text",
            "confidence": 72,
            "perspectives": [
                "English textEnglish textEnglish textEnglish text",
                "English textEnglish text 1 English text",
                "English textEnglish textEnglish text",
            ],
            "nextSteps": [
                "English text 2-3 English text",
                "English text auto English text",
                "English text 24 English text",
            ],
            "risks": [
                "English textEnglish text",
                "English text",
            ],
        },
        "en": {
            "summary": "Pressure-test the reasoning behind {question} before acting.",
            "confidence": 72,
            "perspectives": [
                "Assumption: the way the problem is currently framed captures the most important factors.",
                "Blind spot: an attractive alternative may be easier to imagine than to execute in practice.",
                "Tension: short-term relief or certainty can conflict with long-term goals and optionality.",
            ],
            "nextSteps": [
                "What evidence would make you change your current view?",
                "What important factor is missing because it is difficult to quantify?",
                "What would the downside look like if your main assumption is wrong?",
            ],
            "risks": [
                "Missing information can make a confident conclusion look stronger than it is.",
                "You may be comparing a real option with an idealized alternative.",
            ],
        },
    },
    "rational": {
        "zh-CN": {
            "summary": "English text{question}English text{mode}English textEnglish text",
            "confidence": 78,
            "perspectives": [
                "English textEnglish text 3 English text 3 English text",
                "English textEnglish textEnglish text/English text/English text",
                "English textEnglish textEnglish text",
            ],
            "nextSteps": [
                "English text1-5English text",
                "English textEnglish text",
                "English textEnglish text",
            ],
            "risks": [
                "English text",
                "English text",
            ],
        },
        "en": {
            "summary": "This choice has a real tension between immediate stability and longer-term opportunity.",
            "confidence": 78,
            "perspectives": [
                "Assumption: the current situation cannot improve without making a major change.",
                "Blind spot: switching costs, income stability, references, benefits, and the quality of the alternative may be underweighted.",
                "Tension: short-term security can conflict with learning, autonomy, compensation, or long-term direction.",
            ],
            "nextSteps": [
                "What evidence shows the current situation is unlikely to improve in the next 3–6 months?",
                "What would the alternative need to provide to compensate for its switching costs?",
                "What financial runway and fallback plan would you have if the alternative disappoints?",
            ],
            "risks": [
                "You may be optimizing for relief from today's frustration rather than the best long-term outcome.",
                "You may be comparing a real current option with an idealized version of the alternative.",
            ],
        },
    },
    "random": {
        "zh-CN": {
            "summary": "English text{question}English text{mode}English textEnglish text",
            "confidence": 55,
            "perspectives": [
                "English textEnglish text",
                "English textEnglish text",
                "English textEnglish text",
            ],
            "nextSteps": [
                "English textEnglish text",
                "English textEnglish text",
                "English textEnglish textEnglish text",
            ],
            "risks": [
                "English textEnglish text",
                "English text",
            ],
        },
        "en": {
            "summary": "For {question}, the {mode} mode breaks the deadlock with randomness.",
            "confidence": 55,
            "perspectives": [
                "Coin-flip view: the instinct before the toss reveals a lot.",
                "Surprise view: a random result may expose your hidden lean.",
                "Odds view: estimate each option's chance and note uncertainty.",
            ],
            "nextSteps": [
                "Flip a coin and record which side you hoped for before it lands.",
                "If the result feels wrong, flip again as best-of-three.",
                "Write down why you disagree with the outcome.",
            ],
            "risks": [
                "Taking randomness too seriously and skipping rational analysis.",
                "Using randomness to avoid owning the decision.",
            ],
        },
    },
    "dialogue": {
        "zh-CN": {
            "summary": "English text{question}English text{mode}English text",
            "confidence": 70,
            "perspectives": [
                "English textEnglish textEnglish textEnglish textEnglish textEnglish text",
                "English textEnglish text 5 English text",
                "English textEnglish textEnglish text A English textEnglish text B English text",
            ],
            "nextSteps": [
                "English text 5 English textEnglish text",
                "English text",
                "English text",
            ],
            "risks": [
                "English textEnglish text",
                "English textEnglish text",
            ],
        },
        "en": {
            "summary": "For {question}, the {mode} mode clarifies what you really want through self-dialogue.",
            "confidence": 70,
            "perspectives": [
                "Inner dialogue: let the 'for' and 'against' sides speak.",
                "Future self view: imagine how you'll see this decision in 5 years.",
                "Questioning view: ask 'what do I lose if I pick A? And B?'",
            ],
            "nextSteps": [
                "Ask 'why' five times to dig out the real motive.",
                "Write the internal conflict as a Q&A script.",
                "Ask a friend to play devil's advocate and debate.",
            ],
            "risks": [
                "The dialogue can drag on forever without a decision.",
                "A biased devil's advocate can unbalance the conclusion.",
            ],
        },
    },
    "fengshui": {
        "zh-CN": {
            "summary": "English text{question}English text{mode}English textEnglish text",
            "confidence": 60,
            "perspectives": [
                "English textEnglish text",
                "English textEnglish text",
                "English textEnglish textEnglish text",
            ],
            "nextSteps": [
                "English text",
                "English text",
                "English text",
            ],
            "risks": [
                "English textEnglish text",
                "English textEnglish text",
            ],
        },
        "en": {
            "summary": "For {question}, the {mode} mode gives a directional reading based on bearing, elements, and hour.",
            "confidence": 60,
            "perspectives": [
                "Direction view: the auspicious bearing for your birth chart.",
                "Element view: how the current hour's elements interact with the choice.",
                "Hour view: pick a favorable hour and avoid clashes.",
            ],
            "nextSteps": [
                "Check today's dos/don'ts and your personal favorable direction.",
                "Make the formal decision at a favorable hour and bearing.",
                "Arrange the space afterward to stabilize the result.",
            ],
            "risks": [
                "Bearing and hour calculations can be off; verify solar terms.",
                "Over-relying on fengshui while ignoring real-world constraints.",
            ],
        },
    },
}


def _mock_brief(question: str, mode: str, language: str = "zh-CN") -> Dict[str, Any]:
    """Brief mockEnglish textEnglish text source='mock'"""
    templates = _MOCK_BRIEFS_I18N.get(mode, _MOCK_BRIEFS_I18N["auto"])
    template = templates.get(language, templates["zh-CN"])
    return {
        "summary": template["summary"].format(question=question, mode=mode),
        "confidence": template["confidence"],
        "perspectives": list(template["perspectives"]),
        "nextSteps": list(template["nextSteps"]),
        "risks": list(template["risks"]),
        "source": "mock",
    }


# ─── ModeResultEnglish text API──────────────────────────────────────


def _get_values() -> Dict[str, int]:
    """English text preferences English textrational English text"""
    try:
        from backend.config import get_preferences

        prefs = get_preferences()
        values = prefs.get("values")
        if isinstance(values, dict):
            return values
    except Exception:
        pass
    return {}


def _build_mode_prompt(question: str, mode: str, has_image: bool = False) -> str:
    from backend.services.prompts import founder as founder_prompt
    focus = mode if mode in {"founder", "product", "people", "money", "growth", "conflict"} else "founder"
    prompt = founder_prompt(question, focus)
    if has_image:
        prompt += "\n\nAn image was attached. Use it only as supporting evidence and mention uncertainty where visual evidence is incomplete."
    return prompt


def _mock_random(question: str, language: str = "zh-CN") -> Dict[str, Any]:
    """random mockEnglish textEnglish text 6 English text fallback English text"""
    pools = _RANDOM_POOLS.get(language, _RANDOM_POOLS["zh-CN"])
    if language == "zh-CN":
        if "English text" in question:
            opts = list(pools["eat"])
        elif "English text" in question:
            opts = list(pools["watch"])
        elif "English text" in question:
            opts = list(pools["buy"])
        else:
            opts = list(pools["default"])
    else:
        q = question.lower()
        if any(w in q for w in ("eat", "food", "lunch", "dinner", "restaurant")):
            opts = list(pools["eat"])
        elif any(w in q for w in ("watch", "movie", "film", "show")):
            opts = list(pools["watch"])
        elif any(w in q for w in ("buy", "purchase", "shop")):
            opts = list(pools["buy"])
        else:
            opts = list(pools["default"])
    fallback = _RANDOM_FALLBACK.get(language, _RANDOM_FALLBACK["zh-CN"])
    # English text 6 English text
    for d in fallback:
        if len(opts) >= 6:
            break
        if d not in opts:
            opts.append(d)
    return {"type": "random", "options": opts[:6], "_source": "mock"}


def _mock_fengshui(question: str, language: str = "zh-CN") -> Dict[str, Any]:
    """fengshui mockEnglish text bazi_engine.analyzeEnglish text needBirth=true

    ponytail: bazi_engine English textImportError English text needBirth=true
    English textEnglish text services/bazi_engine.py English text
    """
    is_en = language == "en"
    try:
        from backend.services.bazi_engine import analyze

        bazi = analyze(question)
    except ImportError:
        return {
            "type": "fengshui",
            "needBirth": True,
            "question": (
                "Please provide birth date, time, gender, and birthplace for a complete BaZi chart."
                if is_en else
                "English text bazi-skill English textEnglish textEnglish textEnglish textEnglish text/English text"
            ),
            "bazi": "",
            "wuxing": "",
            "element": "",
            "analysis": "",
            "suggestion": "",
            "baziAudit": "",
            "_source": "mock",
        }

    if not bazi.get("complete"):
        missing = bazi.get("missing", [])
        return {
            "type": "fengshui",
            "needBirth": True,
            "question": (
                f"Missing: {', '.join(missing)}. Please provide birth date, time, gender, and birthplace."
                if is_en else
                f"English text bazi-skill English textEnglish text{''.join(missing)}English textEnglish textEnglish textEnglish text/English text"
            ),
            "bazi": "",
            "wuxing": "",
            "element": "",
            "analysis": "",
            "suggestion": "",
            "baziAudit": bazi.get("audit", ""),
            "_source": "mock",
        }
    pillars = bazi.get("pillars", {})
    return {
        "type": "fengshui",
        "needBirth": False,
        "question": "",
        "bazi": f"{pillars.get('year','')} / {pillars.get('month','')} / {pillars.get('day','')} / {pillars.get('hour','')}",
        "wuxing": bazi.get("wuxing", ""),
        "element": bazi.get("element", ""),
        "analysis": (
            "Basic chart verification only. Full BaZi analysis requires the complete bazi-skill pipeline."
            if is_en else
            "English textEnglish textEnglish textEnglish textEnglish text bazi-skill English textEnglish textEnglish textEnglish text"
        ),
        "suggestion": (
            "Treat this as cultural reference only; for a real BaZi decision, complete the chart first."
            if is_en else
            "English textEnglish textEnglish text bazi-skill English text"
        ),
        "baziAudit": bazi.get("audit", ""),
        "_source": "mock",
    }


def _mock_mode_result(question: str, mode: str, language: str = "zh-CN") -> Dict[str, Any]:
    """mock ModeResultEnglish textEnglish text _source='mock'

    nature English textEnglish text nature_service
    """
    is_en = language == "en"
    if mode == "rational":
        return {
            "type": "rational",
            "pros": [
                "It stops you from overthinking this later" if is_en else "English textEnglish text",
                "You get more used to making your own calls" if is_en else "English textEnglish text",
                "No more carrying it around in your head" if is_en else "English textEnglish text",
            ],
            "cons": [
                "Some short-term pressure and discomfort" if is_en else "English textEnglish text",
                "People around you might have opinions" if is_en else "English text",
            ],
            "conclusion": (
                "Take two small steps first, keep an exit open."
                if is_en else
                "English textEnglish textEnglish textEnglish text"
            ),
            "_source": "mock",
        }
    if mode == "random":
        return _mock_random(question, language=language)
    if mode == "dialogue":
        return {
            "type": "dialogue",
            "question": (
                "Honestly, what would the person you care about most say if they saw you this stuck?"
                if is_en else
                "English textEnglish textEnglish textEnglish text"
            ),
            "options": list(_DIALOGUE_FALLBACK.get(language, _DIALOGUE_FALLBACK["zh-CN"])),
            "_source": "mock",
        }
    if mode == "fengshui":
        return _mock_fengshui(question, language=language)
    if mode == "nature":
        raise ValueError("nature English text nature_service.generate_nature_briefEnglish text llm_service English text")
    # auto English textEnglish textBrief English text + type=auto
    template = _mock_brief(question, mode, language=language)
    return {
        "type": "auto",
        "summary": template["summary"],
        "confidence": template["confidence"],
        "perspectives": list(template["perspectives"]),
        "nextSteps": list(template["nextSteps"]),
        "risks": list(template["risks"]),
        "_source": "mock",
    }


def _text(value: Any, max_len: int = 240) -> str:
    """English textEnglish text + English text"""
    return str(value if value is not None else "").replace("\x00", "").strip()[:max_len]


def _array(value: Any, max_items: int = 8, max_text: int = 120) -> list:
    """English textEnglish text + English text + English text"""
    if not isinstance(value, list):
        return []
    arr = [_text(v, max_text) for v in value[:max_items]]
    return [a for a in arr if a]


def sanitize_result(raw: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """schema English textEnglish text HTML English text AI._sanitize

    Args:
        raw: LLM English text dictEnglish text
        mode: English text

    Returns:
        English text dictEnglish text fallback English textEnglish text _source English text _schemaWarning
    """
    if not isinstance(raw, dict):
        return {"type": mode, "_source": "real", "_schemaWarning": "English text dict"}

    valid_types = {"rational", "random", "nature", "dialogue", "fengshui"}
    type_ = raw.get("type") if raw.get("type") in valid_types else mode

    warnings: list = []
    base = {"type": type_, "_source": raw.get("_source", "real")}

    def ensure_text(value: Any, fallback: str, max_len: int = 240) -> str:
        text = _text(value, max_len)
        if not text:
            warnings.append(fallback)
        return text or fallback

    def ensure_array(value: Any, fallback: list, min_items: int = 1,
                     max_items: int = 8, max_text: int = 120) -> list:
        arr = _array(value, max_items, max_text)
        if len(arr) < min_items:
            warnings.append(" / ".join(fallback))
        return arr if len(arr) >= min_items else list(fallback)

    def done(data: Dict[str, Any]) -> Dict[str, Any]:
        if warnings:
            data["_schemaWarning"] = "".join(warnings[:4])
        return data

    if type_ == "rational":
        return done({**base,
                     "pros": ensure_array(raw.get("pros"), ["English text"], 1, 6),
                     "cons": ensure_array(raw.get("cons"), ["English text"], 1, 6),
                     "conclusion": ensure_text(raw.get("conclusion"), "English textEnglish text", 220)})
    if type_ == "random":
        return done({**base,
                     "options": ensure_array(raw.get("options"), list(_RANDOM_FALLBACK["zh-CN"]), 6, 8, 50),
                     "reason": _text(raw.get("reason"), 160)})
    if type_ == "nature":
        return done({**base,
                     "time": ensure_text(raw.get("time"), "English text", 30),
                     "season": ensure_text(raw.get("season"), "English text", 20),
                     "weather": ensure_text(raw.get("weather"), "English text", 40),
                     "sun": _text(raw.get("sun"), 60),
                     "wind": _text(raw.get("wind"), 60),
                     "source": ensure_text(raw.get("source"), "English text", 80),
                     "isReal": bool(raw.get("isReal")),
                     "signal": ensure_text(raw.get("signal"), "English text", 80),
                     "poem": ensure_text(raw.get("poem"), "English textEnglish text", 260),
                     "suggestion": ensure_text(raw.get("suggestion"), "English text", 180)})
    if type_ == "dialogue":
        return done({**base,
                     "question": ensure_text(raw.get("question"), "English text", 180),
                     "options": ensure_array(raw.get("options"), list(_DIALOGUE_FALLBACK["zh-CN"]), 3, 4, 80)})
    if type_ == "fengshui":
        need_birth = bool(raw.get("needBirth"))
        return done({**base,
                     "needBirth": need_birth,
                     "question": _text(raw.get("question"), 240),
                     "bazi": ensure_text(raw.get("bazi"), "" if need_birth else "English text", 200),
                     "wuxing": _text(raw.get("wuxing"), 240),
                     "element": _text(raw.get("element"), 120),
                     "analysis": ensure_text(raw.get("analysis"),
                                             "English text" if need_birth else "English text", 360),
                     "suggestion": ensure_text(raw.get("suggestion"), "English textEnglish text", 200),
                     "baziAudit": _text(raw.get("baziAudit"), 260)})
    # auto English textEnglish text
    return done({**base, **{k: v for k, v in raw.items() if k != "type"}})


class NoApiKeyError(Exception):
    """English text API Key English text demo_mode English text"""
    pass


def call_llm(question: str, mode: str, config: Optional[Dict[str, Any]] = None,
             language: str = "zh-CN", allow_mock: bool = False,
             image: Optional[str] = None) -> Dict[str, Any]:
    """English text LLM English text ModeResult

    config English text None English text get_effective_config() English text
    allow_mock=True English textEnglish textEnglish text/English text mockEnglish text _source='mock'
    allow_mock=False English textEnglish text NoApiKeyErrorEnglish text
    image English text base64 data URLEnglish text

    nature English textEnglish text nature_service
    """
    if mode == "nature":
        raise ValueError("nature English text nature_service.generate_nature_briefEnglish text llm_service English text")

    if config is None:
        config = get_effective_config()

    has_image = bool(image and isinstance(image, str) and image.startswith("data:"))

    if has_llm_config(config):
        try:
            prompt = _build_mode_prompt(question, mode, has_image=has_image)
            raw = call_openai_llm(prompt, config, image=(image if has_image else None))
            raw["_source"] = "real"
            return sanitize_result(raw, mode)
        except Exception as e:
            # English text api_keyEnglish text
            print(f"[llm] English text: {type(e).__name__}")
            if not allow_mock:
                raise
            print(f"[llm] allow_mock=TrueEnglish text mock")

    if not allow_mock:
        raise NoApiKeyError("English text LLM API KeyEnglish text Demo English text")

    return _mock_mode_result(question, mode, language=language)


# ─── English text API English text ─────────────────────────────────────────────


def generate_brief(question: str, mode: str, config: Optional[Dict[str, Any]] = None) -> Brief:
    """English textEnglish text API

    English text Brief English text prompt + Brief mockEnglish text call_llm English text ModeResult English text
    """
    if config is None:
        config = get_effective_config()

    if has_llm_config(config):
        try:
            data = call_openai_llm(_build_brief_prompt(question, mode), config)
            data["source"] = "real"
        except Exception as e:
            print(f"[llm] English textEnglish text mock: {type(e).__name__}")
            data = _mock_brief(question, mode)
    else:
        data = _mock_brief(question, mode)

    fields = Brief.model_fields if hasattr(Brief, "model_fields") else Brief.__fields__
    return Brief(**{k: v for k, v in data.items() if k in fields})


def generate_reply(question: str, mode: str, brief: Brief) -> str:
    """English text"""
    return (
        f"English text{mode}English text{question}\n"
        f"English text{brief.summary}\n"
        f"English text{brief.confidence}/100English text"
    )
