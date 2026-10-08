"""English text/api/config + /api/preferences

- GET  /api/config        English text LLM/English text
- POST /api/config        English text API Key English text SQLiteEnglish text
- DELETE /api/config      English text API Key English text
- GET  /api/preferences   English text
- POST /api/preferences   English text

English textapiKey/weather_key English textEnglish text

English text v0.7.0 English textweather.hasKey English text hasAppid/hasAppsecret
"""

from typing import Any, Dict

from fastapi import APIRouter

from backend import config as config_mod
from backend import db
from backend.models.schemas import ConfigUpdate, PreferencesUpdate

router = APIRouter()


def _to_config_response(masked: Dict[str, Any]) -> Dict[str, Any]:
    """English text get_masked_config() English text ConfigResponse English text"""
    has_key = bool(masked.get("llm_api_key"))
    # Key English text Base URL English textweather_appsecret English text
    has_weather_key = bool(masked.get("weather_key") or masked.get("weather_appsecret"))
    return {
        "llm": {
            "model": masked.get("llm_model", ""),
            "baseUrl": masked.get("llm_base_url", ""),
            "hasKey": has_key,
        },
        "weather": {
            "city": masked.get("weather_city", ""),
            "baseUrl": masked.get("weather_base_url", ""),
            "hasKey": has_weather_key,
            "hasBaseUrl": bool(masked.get("weather_base_url")),
            # English textEnglish text hasAppsecret
            "hasAppsecret": has_weather_key,
        },
        "hasLlm": config_mod.has_llm_config(masked),
        "hasWeather": config_mod.has_weather_config(masked),
    }


# ─── /api/config ───────────────────────────────────────────────


@router.get("/api/config")
def get_config() -> Dict[str, Any]:
    """English text LLM/English text + hasLlm/hasWeather"""
    masked = config_mod.get_masked_config()
    return _to_config_response(masked)


@router.post("/api/config")
def save_config(body: ConfigUpdate) -> Dict[str, Any]:
    """English text API Key English text SQLiteEnglish text None English text"""
    payload = body.model_dump(exclude_none=True)
    # English textEnglish text
    payload = {k: v for k, v in payload.items() if v}
    masked = config_mod.save_api_keys_to_db(payload)
    return _to_config_response(masked)


@router.delete("/api/config")
def clear_config() -> Dict[str, Any]:
    """English text API Key English textEnglish text"""
    for key in config_mod.CONFIG_KEYS:
        db.delete_config_value(key)
    return {"ok": True}


# ─── /api/preferences ─────────────────────────────────────────


@router.get("/api/preferences")
def get_preferences() -> Dict[str, Any]:
    """English textEnglish text + SQLiteEnglish text"""
    return config_mod.get_preferences()


@router.post("/api/preferences")
def save_preferences(body: PreferencesUpdate) -> Dict[str, Any]:
    """English text SQLiteEnglish text"""
    payload = body.model_dump(exclude_none=True)
    return config_mod.save_preferences(payload)
