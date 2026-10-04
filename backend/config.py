"""English textEnglish text

English text
  1. English textCHOICE_LLM_API_KEY / CHOICE_LLM_MODEL / CHOICE_LLM_BASE_URL
              CHOICE_WEATHER_KEY / CHOICE_WEATHER_BASE_URL / CHOICE_WEATHER_CITY
  2. SQLite config English textUI English textEnglish text choice.db
  3. ~/.choice/config.jsonCLI config --save English textEnglish text 0600English text

English text
  - API Key English text
  - English text llm_api_key / weather_key English text ***English text***
  - ponytail: SQLite English text API Key English textEnglish text AES-256-GCM English text

English text v0.7.0 English textEnglish text
  - English textweather_keyEnglish text Key + weather_base_url + weather_city
  - English textweather_appsecretEnglish text KeyEnglish text weather_key
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# English textEnglish text CLI English text
CONFIG_FILE_PATH = Path.home() / ".choice" / "config.json"

# English text
CONFIG_KEYS = (
    "llm_api_key",
    "llm_model",
    "llm_base_url",
    "weather_key",       # English textEnglish text Key
    "weather_base_url",  # English textEnglish text
    "weather_appsecret", # English textEnglish text KeyEnglish text weather_key
    "weather_city",
)

# English text
ENV_KEY_MAP = {
    "llm_api_key": "CHOICE_LLM_API_KEY",
    "llm_model": "CHOICE_LLM_MODEL",
    "llm_base_url": "CHOICE_LLM_BASE_URL",
    "weather_key": "CHOICE_WEATHER_KEY",
    "weather_base_url": "CHOICE_WEATHER_BASE_URL",
    "weather_appsecret": "CHOICE_WEATHER_APPSECRET",  # English text
    "weather_city": "CHOICE_WEATHER_CITY",
}

# English textEnglish text
SENSITIVE_KEYS = ("llm_api_key", "weather_key", "weather_appsecret")

def _read_config_file() -> Dict[str, Any]:
    """English text ~/.choice/config.json English textEnglish text dict"""
    if not CONFIG_FILE_PATH.exists():
        return {}
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config_file(partial: Dict[str, Any]) -> Dict[str, Any]:
    """English text ~/.choice/config.jsonEnglish text 0600"""
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(_read_config_file())
    for k, v in partial.items():
        if v is not None:
            merged[k] = v
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_FILE_PATH, 0o600)
    except OSError:
        pass  # Windows best-effort
    return merged


def get_effective_config() -> Dict[str, Any]:
    """English text API Key English textEnglish text > SQLite > config.json

    English textEnglish text api_keyEnglish text
    """
    # English text SQLite English textEnglish text
    from db import get_all_config

    cfg: Dict[str, Any] = {k: "" for k in CONFIG_KEYS}

    # English text 3config.json
    file_cfg = _read_config_file()
    for k in CONFIG_KEYS:
        if file_cfg.get(k):
            cfg[k] = file_cfg[k]

    # English text 2SQLite config English textEnglish text config.json
    db_cfg = get_all_config()
    for k in CONFIG_KEYS:
        if db_cfg.get(k):
            cfg[k] = db_cfg[k]

    # English text 1English textEnglish text
    for k, env in ENV_KEY_MAP.items():
        val = os.environ.get(env)
        if val:
            cfg[k] = val

    return cfg


def get_masked_config() -> Dict[str, Any]:
    """English textEnglish text UI English text CLI English text"""
    cfg = get_effective_config()
    for k in SENSITIVE_KEYS:
        if cfg.get(k):
            cfg[k] = "***English text***"
    return cfg


def save_api_keys_to_db(config: Dict[str, Any]) -> Dict[str, Any]:
    """English text API Key English text SQLite config English textUI English text

    English text None English text
    """
    from db import set_config_value

    for k in CONFIG_KEYS:
        val = config.get(k)
        if val:
            set_config_value(k, val)
    return get_masked_config()


def save_api_keys_to_file(config: Dict[str, Any]) -> Dict[str, Any]:
    """English text API Key English text ~/.choice/config.jsonCLI config --save English text"""
    partial = {k: v for k, v in config.items() if k in CONFIG_KEYS and v is not None}
    merged = _save_config_file(partial)
    masked = dict(merged)
    for k in SENSITIVE_KEYS:
        if masked.get(k):
            masked[k] = "***English text***"
    return masked


def has_llm_config(config: Dict[str, Any] = None) -> bool:
    """English text LLM English text"""
    cfg = config or get_effective_config()
    return bool(cfg.get("llm_api_key") and cfg.get("llm_base_url") and cfg.get("llm_model"))


def has_weather_config(config: Dict[str, Any] = None) -> bool:
    """English text API English text

    English text weather_key English text weather_base_urlcity English textEnglish text
    English textweather_appsecret English text key English text
    """
    cfg = config or get_effective_config()
    return bool((cfg.get("weather_key") or cfg.get("weather_appsecret")) and cfg.get("weather_base_url"))


# ─── English textpreferences─────────────────────────────────────

PREF_KEYS = (
    "language",        # 'zh-CN' / 'yue' / 'en' / 'fr' / 'ja' / 'es'
    "default_mode",    # 'auto' / 'rational' / 'random' / 'nature' / 'dialogue' / 'fengshui'
    "theme",           # 'light' / 'dark' / 'auto'
    "skin",            # 'heritage' / 'workbench' / 'journal' / 'console'
    "logo",            # Logo id
    "auto_speak",      # bool
    "tts_rate",        # float 0.5-1.5
    "tts_pitch",       # float 0.5-1.5
    "tts_voice_uri",   # string
    "values",          # {efficiency, risk, growth, relationship} 0-100
    "demo_mode",       # bool: English text API Key English text mock English text
)

DEFAULT_PREFS: Dict[str, Any] = {
    "language": "en",
    "default_mode": "auto",
    "theme": "auto",
    "skin": "heritage",
    "logo": "tree1",
    "auto_speak": True,
    "tts_rate": 0.95,
    "tts_pitch": 1.05,
    "tts_voice_uri": "zh-CN-XiaoxiaoNeural",
    "values": {"efficiency": 60, "risk": 50, "growth": 70, "relationship": 55},
    "demo_mode": False,
}


def get_preferences() -> Dict[str, Any]:
    """English textEnglish text + SQLiteEnglish textEnglish text"""
    from db import get_config_value

    prefs = dict(DEFAULT_PREFS)
    stored = get_config_value("preferences", {})
    if isinstance(stored, dict):
        for k, v in stored.items():
            if v == "" and k in DEFAULT_PREFS and DEFAULT_PREFS[k]:
                continue
            prefs[k] = v
    return prefs


def save_preferences(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """English text SQLite"""
    from db import set_config_value

    current = get_preferences()
    current.update({k: v for k, v in prefs.items() if k in PREF_KEYS})
    set_config_value("preferences", current)
    return current
