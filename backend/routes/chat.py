"""POST /api/chat - English text + English textEnglish text AI English text

English text
  1. English textapiKey/llmModel/... > English text > SQLite > config.json
  2. mode == "auto" English text mode_recognizer.explain English text
  3. mode == "nature" English text nature_service.generate_nature_brief
  4. English text llm_service.call_llm English text ModeResult dict
  5. English text SQLite decisions English text
  6. English text ChatResponsebrief/nature/mode/reply/result/autoRecognized
"""

from typing import Any, Dict, Optional
import os

from fastapi import APIRouter, HTTPException

import db
from config import get_effective_config, get_preferences
from models.schemas import Brief, ChatRequest, ChatResponse
from services.llm_service import NoApiKeyError, call_llm
from services.mode_recognizer import explain as explain_mode
from services.nature_service import generate_nature_brief

router = APIRouter()


def _request_overrides(req: ChatRequest) -> dict:
    """English textEnglish text config English text

    v0.7.0 English text weatherKeyEnglish text KeyEnglish text
    weatherAppsecret English textEnglish text weather_key
    """
    weather_key = req.weatherKey or req.weatherAppsecret
    return {
        "llm_api_key": req.apiKey,
        "llm_model": req.llmModel,
        "llm_base_url": req.llmBaseUrl,
        "weather_key": weather_key,
        "weather_base_url": req.weatherBaseUrl,
        "weather_appsecret": req.weatherAppsecret,
        "weather_city": req.weatherCity,
    }


def _merge_overrides(base: dict, overrides: dict) -> dict:
    """English text base English textEnglish text"""
    cfg = dict(base)
    if not overrides:
        return cfg
    for k, v in overrides.items():
        if v:
            cfg[k] = v
    return cfg


def _try_build_brief(result: Dict[str, Any], mode: str = "auto") -> Optional[Brief]:
    """English text ModeResult English text Brief

    English text result English text summary/confidence/perspectives/nextSteps/risks
    English textconclusion/signal/suggestion/pros/cons
    confidence English textEnglish text
    """
    if not isinstance(result, dict):
        return None

    # English textEnglish text llm_service._MOCK_BRIEFS English text
    default_confidence = {
        "rational": 78,
        "random": 55,
        "nature": 65,
        "dialogue": 70,
        "fengshui": 60,
        "auto": 72,
    }.get(mode, 60)

    summary = (
        result.get("summary")
        or result.get("conclusion")
        or result.get("signal")
        or result.get("suggestion")
        or ""
    )
    confidence = result.get("confidence")
    if confidence is None:
        confidence = default_confidence
    try:
        confidence = int(confidence)
    except (TypeError, ValueError):
        confidence = default_confidence

    perspectives = list(result.get("perspectives", []) or [])
    next_steps = list(result.get("nextSteps", []) or [])
    risks = list(result.get("risks", []) or [])

    # English text perspectives / risks
    if not perspectives:
        pros = result.get("pros") or []
        cons = result.get("cons") or []
        if pros:
            perspectives.append("Potential upside: " + "; ".join(str(p) for p in pros[:3]))
        if cons:
            risks.append("Potential downside: " + "; ".join(str(c) for c in cons[:3]))
    if not next_steps and result.get("suggestion"):
        next_steps.append(str(result["suggestion"]))

    if not summary:
        return None

    try:
        return Brief(
            summary=summary,
            confidence=confidence,
            perspectives=perspectives,
            nextSteps=next_steps,
            risks=risks,
            source=result.get("source") or result.get("_source"),
        )
    except (TypeError, ValueError):
        return None


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """English text + English textEnglish text

    - auto English textEnglish text mode_recognizer.explain English textEnglish text autoRecognized
    - nature English textEnglish text nature_servicebrief English text
    - English textEnglish text call_llm English text ModeResultEnglish text result English text Brief
    - English text decisions English text
    """
    if req.provider == "free" and not os.environ.get("FOUNDEROS_FREE_AI_API_KEY"):
        raise HTTPException(status_code=503, detail="FounderOS Free AI is not configured on this deployment yet.")
    if req.provider == "byok" and not req.apiKey:
        raise HTTPException(status_code=402, detail="Choose Use my API key and provide a key for this request.")
    overrides = _request_overrides(req)
    if req.provider == "free":
        overrides.update({
            "llm_api_key": os.environ.get("FOUNDEROS_FREE_AI_API_KEY", ""),
            "llm_model": (
                os.environ.get("FOUNDEROS_FREE_AI_MODEL", "").strip()
                if os.environ.get("FOUNDEROS_FREE_AI_MODEL", "").strip()
                not in {"qwen/qwen3.8-27b:free", "qwen/qwen3.8-27b"}
                else "nvidia/nemotron-3.5-lightning:free"
            ),
            "llm_base_url": os.environ.get(
                "FOUNDEROS_FREE_AI_BASE_URL",
                "https://openrouter.ai/api/v1",
            ),
            "llm_fallback_models": os.environ.get(
                "FOUNDEROS_FREE_AI_FALLBACK_MODELS",
                "openrouter/free",
            ),
        })
    merged_config = _merge_overrides(get_effective_config(), overrides)

    # English textEnglish text Key English text mock English textdemo_mode English text mock English text
    prefs = get_preferences()
    language = prefs.get("language", "zh-CN")
    allow_mock = bool(prefs.get("demo_mode", False))

    # 1. auto English text
    auto_recognized: Optional[Dict[str, Any]] = None
    effective_mode = req.mode
    if effective_mode == "auto":
        auto_recognized = explain_mode(req.question)
        effective_mode = str(auto_recognized.get("mode") or "auto")

    # 2. English text
    brief: Optional[Brief] = None
    nature: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    reply: str = ""

    try:
        if effective_mode == "nature":
            nature = generate_nature_brief(req.question, config=merged_config,
                                           language=language, allow_mock=allow_mock)
            result = nature
            signal = nature.get("signal", "")
            poem = nature.get("poem", "")
            suggestion = nature.get("suggestion", "")
            reply = (
                f"Nature context for: {req.question}\n"
                f"Signal to examine: {signal}\n"
                f"{poem}\n"
                f"Reflection: {suggestion}"
            )
        else:
            result = call_llm(req.question, effective_mode, merged_config,
                              language=language, allow_mock=allow_mock,
                              image=req.image)
            brief = _try_build_brief(result, mode=effective_mode)
            summary = result.get("summary") or result.get("conclusion") or ""
            reply = (
                f"{effective_mode.title()} analysis for: {req.question}\n"
                f"{summary}"
            )
    except NoApiKeyError:
        raise HTTPException(status_code=402, detail="No LLM API key is configured. Add one in settings or enable demo mode.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)[:500])

    # 3. English text
    decision_id: Optional[str] = None
    try:
        saved = db.save_decision({
            "question": req.question,
            "mode": effective_mode,
            "result": result or {},
            "brief": brief.model_dump() if brief else None,
            "executed": False,
            "regret": False,
        })
        decision_id = saved.get("id")
    except Exception as e:
        # English text
        print(f"[chat] English text: {type(e).__name__}")

    # 4. English text
    return ChatResponse(
        brief=brief,
        nature=nature,
        mode=effective_mode,
        reply=reply,
        result=result,
        autoRecognized=auto_recognized,
        decisionId=decision_id,
    )
