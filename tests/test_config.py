"""English textconfig.pyEnglish text

English textenv > db > fileEnglish texthas_llm_config/has_weather_config
save_api_keys_to_dbpreferences
"""

import os

import config as config_mod
import db


# ─── English text ──────────────────────────────────────────────


def test_get_effective_config_layer_priority_env_over_db_over_file(monkeypatch):
    """English text > SQLite > config.jsonEnglish text"""
    # English text 3config.json
    config_mod._save_config_file({"llm_api_key": "from-file", "llm_model": "gpt-file"})

    # English text 2SQLite
    db.set_config_value("llm_api_key", "from-db")
    db.set_config_value("llm_model", "gpt-db")

    # English text 1English text
    monkeypatch.setenv("CHOICE_LLM_API_KEY", "from-env")

    cfg = config_mod.get_effective_config()
    assert cfg["llm_api_key"] == "from-env"  # English text
    assert cfg["llm_model"] == "gpt-db"  # English text


def test_get_effective_config_db_over_file(monkeypatch):
    """English textSQLite English text config.json"""
    # English text
    for env in ("CHOICE_LLM_API_KEY", "CHOICE_LLM_MODEL", "CHOICE_LLM_BASE_URL"):
        monkeypatch.delenv(env, raising=False)

    config_mod._save_config_file({"llm_api_key": "from-file"})
    db.set_config_value("llm_api_key", "from-db")

    cfg = config_mod.get_effective_config()
    assert cfg["llm_api_key"] == "from-db"


def test_get_effective_config_file_fallback(monkeypatch):
    """English textEnglish text SQLite English textEnglish text config.json"""
    for env in ("CHOICE_LLM_API_KEY", "CHOICE_LLM_MODEL", "CHOICE_LLM_BASE_URL"):
        monkeypatch.delenv(env, raising=False)

    config_mod._save_config_file({"llm_api_key": "from-file-only"})

    cfg = config_mod.get_effective_config()
    assert cfg["llm_api_key"] == "from-file-only"


def test_get_effective_config_default_empty(monkeypatch):
    """English textEnglish text"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)

    cfg = config_mod.get_effective_config()
    for key in config_mod.CONFIG_KEYS:
        assert cfg[key] == ""


# ─── English text ────────────────────────────────────────────────────


def test_get_masked_config_masks_sensitive_fields(monkeypatch):
    """llm_api_key / weather_key / weather_appsecret English text ***English text***English text"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)

    db.set_config_value("llm_api_key", "sk-real-secret")
    db.set_config_value("weather_key", "amap-real-key")
    db.set_config_value("weather_base_url", "https://restapi.amap.com/v3/weather/weatherInfo")
    db.set_config_value("llm_model", "gpt-4o-mini")
    db.set_config_value("weather_city", "English text")

    masked = config_mod.get_masked_config()
    assert masked["llm_api_key"] == "***English text***"
    assert masked["weather_key"] == "***English text***"
    # English text
    assert masked["llm_model"] == "gpt-4o-mini"
    assert masked["weather_city"] == "English text"
    assert masked["weather_base_url"] == "https://restapi.amap.com/v3/weather/weatherInfo"


def test_get_masked_config_empty_when_not_set(monkeypatch):
    """English text"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)

    masked = config_mod.get_masked_config()
    assert masked["llm_api_key"] == ""
    assert masked["weather_key"] == ""
    assert masked["weather_appsecret"] == ""


# ─── has_llm_config / has_weather_config ────────────────────


def test_has_llm_config_requires_all_three(monkeypatch):
    """English text api_key + base_url + model English text True"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)

    assert config_mod.has_llm_config() is False

    db.set_config_value("llm_api_key", "sk-1")
    assert config_mod.has_llm_config() is False  # English text base_url English text model

    db.set_config_value("llm_base_url", "https://api.openai.com/v1")
    assert config_mod.has_llm_config() is False  # English text model

    db.set_config_value("llm_model", "gpt-4o-mini")
    assert config_mod.has_llm_config() is True


def test_has_weather_config_accepts_user_and_legacy_keys(monkeypatch):
    """English text Key English text FalseEnglish text appsecret"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)

    assert config_mod.has_weather_config() is False
    assert config_mod.has_weather_config({"weather_key": "", "weather_appsecret": "", "sentinel": True}) is False
    assert config_mod.has_weather_config({"weather_key": "amap-key"}) is False
    assert config_mod.has_weather_config({
        "weather_key": "amap-key",
        "weather_base_url": "https://restapi.amap.com/v3/weather/weatherInfo",
    }) is True
    assert config_mod.has_weather_config({
        "weather_appsecret": "legacy-key",
        "weather_base_url": "https://restapi.amap.com/v3/weather/weatherInfo",
    }) is True


def test_has_llm_config_env_overrides(monkeypatch):
    """English text"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setenv("CHOICE_LLM_API_KEY", "env-key")
    monkeypatch.setenv("CHOICE_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("CHOICE_LLM_MODEL", "gpt-4o-mini")

    assert config_mod.has_llm_config() is True


# ─── save_api_keys_to_db ────────────────────────────────────


def test_save_api_keys_to_db_persists_to_sqlite(monkeypatch):
    """English text SQLite config English textEnglish textEnglish text"""
    for env in list(config_mod.ENV_KEY_MAP.values()):
        monkeypatch.delenv(env, raising=False)

    masked = config_mod.save_api_keys_to_db(
        {
            "llm_api_key": "sk-persist",
            "llm_model": "gpt-4o-mini",
            "llm_base_url": "https://api.openai.com/v1",
            "weather_appid": "",  # English text
            "weather_appsecret": None,  # None English text
        }
    )

    # English text
    assert masked["llm_api_key"] == "***English text***"
    assert masked["llm_model"] == "gpt-4o-mini"

    # English text
    assert db.get_config_value("llm_api_key") == "sk-persist"
    assert db.get_config_value("llm_model") == "gpt-4o-mini"
    assert db.get_config_value("llm_base_url") == "https://api.openai.com/v1"
    # English text
    assert db.get_config_value("weather_appid", default="<missing>") == "<missing>"


# ─── preferences ────────────────────────────────────────────


def test_get_preferences_returns_defaults_when_empty():
    """English textEnglish text"""
    prefs = config_mod.get_preferences()
    assert prefs["language"] == "zh-CN"
    assert prefs["default_mode"] == "auto"
    assert prefs["theme"] == "auto"
    assert prefs["skin"] == "heritage"
    assert prefs["auto_speak"] is True
    assert prefs["tts_rate"] == 0.95
    assert prefs["tts_pitch"] == 1.05
    assert prefs["values"]["efficiency"] == 60
    assert prefs["values"]["risk"] == 50


def test_save_preferences_merges_with_defaults():
    """save_preferences English textEnglish text"""
    saved = config_mod.save_preferences({"language": "yue", "theme": "dark"})
    assert saved["language"] == "yue"
    assert saved["theme"] == "dark"
    # English text
    assert saved["default_mode"] == "auto"
    assert saved["auto_speak"] is True

    # English text get English text
    prefs = config_mod.get_preferences()
    assert prefs["language"] == "yue"
    assert prefs["theme"] == "dark"


def test_save_preferences_persists_skin():
    saved = config_mod.save_preferences({"skin": "journal"})
    assert saved["skin"] == "journal"
    assert config_mod.get_preferences()["skin"] == "journal"


def test_save_preferences_ignores_unknown_keys():
    """English textEnglish text"""
    saved = config_mod.save_preferences({"language": "en", "unknown_key": "should-be-ignored"})
    assert "unknown_key" not in saved
    assert saved["language"] == "en"
