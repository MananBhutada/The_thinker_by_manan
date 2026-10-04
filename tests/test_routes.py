"""API English textFastAPI TestClient

English text conftest.py English text isolate_paths fixture English text
  - DB_PATH English text
  - CONFIG_FILE_PATH English text
  - English text DemoEnglish text /api/chat English text mock English textEnglish text LLM English text
"""

import pytest
from fastapi.testclient import TestClient

import main
import config as config_mod


@pytest.fixture
def client():
    """English text TestClientDB English text conftest.isolate_paths English text"""
    config_mod.save_preferences({"demo_mode": True})
    with TestClient(main.app) as c:
        yield c


# ─── English text ────────────────────────────────────────────────────


def test_health(client):
    """GET /api/health English text 200 English text ok English text"""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["name"] == "English text API"
    assert "version" in body


def test_get_modes(client):
    """GET /api/modes English text 6 English text + 5 English text"""
    resp = client.get("/api/modes")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["modes"]) == 6
    mode_ids = {m["id"] for m in body["modes"]}
    assert mode_ids == {"auto", "rational", "random", "nature", "dialogue", "fengshui"}
    # English text name/icon/color/description
    for m in body["modes"]:
        assert m["name"]
        assert m["icon"]
        assert m["color"]
        assert m["description"]
    assert len(body["quickQuestions"]) == 5


# ─── English text ────────────────────────────────────────────────────


def test_get_config_returns_masked(client):
    """GET /api/config English text

    weather.hasKey English text KeyhasAppsecret English text
    """
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm"]["hasKey"] is False
    assert body["weather"]["hasKey"] is False
    assert body["weather"]["hasBaseUrl"] is False
    assert body["weather"]["hasAppsecret"] is False  # English textEnglish text hasKey
    assert body["hasLlm"] is False
    assert body["hasWeather"] is False


def test_post_config_then_get_shows_has_key(client):
    """POST /api/config English text GET English text hasKey=true"""
    payload = {
        "llm_api_key": "sk-test-xxx",
        "llm_model": "gpt-4o-mini",
        "llm_base_url": "https://api.openai.com/v1",
    }
    resp = client.post("/api/config", json=payload)
    assert resp.status_code == 200
    assert resp.json()["llm"]["hasKey"] is True

    # GET English text
    resp = client.get("/api/config")
    body = resp.json()
    assert body["llm"]["hasKey"] is True
    assert body["llm"]["model"] == "gpt-4o-mini"
    assert body["llm"]["baseUrl"] == "https://api.openai.com/v1"
    # apiKey English text
    assert "sk-test-xxx" not in resp.text


def test_post_weather_config_requires_key_and_base_url(client):
    resp = client.post("/api/config", json={"weather_key": "amap-test-key", "weather_city": "English text"})
    assert resp.status_code == 200
    assert resp.json()["weather"]["hasKey"] is True
    assert resp.json()["hasWeather"] is False

    resp = client.post("/api/config", json={
        "weather_base_url": "https://restapi.amap.com/v3/weather/weatherInfo",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["weather"]["baseUrl"] == "https://restapi.amap.com/v3/weather/weatherInfo"
    assert body["weather"]["hasBaseUrl"] is True
    assert body["hasWeather"] is True


# ─── /api/chat ──────────────────────────────────────────────


def test_chat_auto_recognizes_random_mode(client):
    """POST /api/chat {mode:auto} English textEnglish textEnglish text random"""
    resp = client.post("/api/chat", json={"question": "English text", "mode": "auto"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "random"
    assert body["autoRecognized"] is not None
    assert body["autoRecognized"]["mode"] == "random"
    assert "reason" in body["autoRecognized"]
    assert "confidence" in body["autoRecognized"]
    # mock English text
    assert body["result"]["_source"] == "mock"
    # English text
    assert body["decisionId"]


def test_chat_random_returns_six_options(client):
    """POST /api/chat {mode:random} English text result.options 6 English text"""
    resp = client.post("/api/chat", json={"question": "English text", "mode": "random"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "random"
    result = body["result"]
    assert result["type"] == "random"
    assert len(result["options"]) == 6
    assert all(isinstance(o, str) and o for o in result["options"])


def test_chat_rational_returns_pros_and_cons(client):
    """POST /api/chat {mode:rational} English text result.pros/cons English text

    rational mock English text result English text conclusion English text summaryEnglish text brief English text None English text
    _try_build_brief English text result English text summary English text confidence English text
    """
    resp = client.post("/api/chat", json={"question": "English text", "mode": "rational"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "rational"
    result = body["result"]
    assert result["type"] == "rational"
    assert isinstance(result["pros"], list) and len(result["pros"]) >= 1
    assert isinstance(result["cons"], list) and len(result["cons"]) >= 1
    # rational mock English text conclusion English text
    assert result.get("conclusion")
    # English text
    assert body["decisionId"]


def test_chat_nature_returns_nature_brief(client):
    """POST /api/chat {mode:nature} English text nature English text null"""
    resp = client.post("/api/chat", json={"question": "English text", "mode": "nature"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "nature"
    assert body["nature"] is not None
    # nature English text signal/poem/suggestion
    assert body["nature"]["signal"]
    assert body["nature"]["poem"]
    assert body["nature"]["suggestion"]
    assert body["nature"]["moonPhase"]
    assert body["nature"]["weatherStatus"] == "not_configured"
    assert body["nature"]["signals"]["weights"]
    # nature English text brief English text null
    assert body["brief"] is None


def test_chat_fengshui_returns_need_birth(client):
    """POST /api/chat {mode:fengshui} English text result.needBirth=true"""
    resp = client.post("/api/chat", json={"question": "English text", "mode": "fengshui"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "fengshui"
    result = body["result"]
    assert result["type"] == "fengshui"
    assert result["needBirth"] is True


# ─── /api/decision CRUD ─────────────────────────────────────


def test_decision_crud_full_cycle(client):
    """POST English text → GET English text → PATCH English text → DELETE English text English text"""
    # 1. English text
    payload = {
        "question": "English text",
        "mode": "rational",
        "result": {"type": "rational", "pros": ["a"], "cons": ["b"]},
    }
    resp = client.post("/api/decision", json=payload)
    assert resp.status_code == 200
    created = resp.json()
    assert created["id"]
    assert created["createdAt"]
    decision_id = created["id"]

    # 2. English text
    resp = client.get(f"/api/decision/{decision_id}")
    assert resp.status_code == 200
    assert resp.json()["question"] == "English text"

    # 3. English text
    resp = client.patch(
        f"/api/decision/{decision_id}",
        json={"executed": True, "regret": False, "dialogueHistory": [{"role": "user", "text": "done"}]},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["executed"] is True
    assert updated["regret"] is False
    assert updated["dialogueHistory"] == [{"role": "user", "text": "done"}]

    # 4. English text
    resp = client.delete(f"/api/decision/{decision_id}")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # 5. English text GET English text 404
    resp = client.get(f"/api/decision/{decision_id}")
    assert resp.status_code == 404


def test_decision_get_returns_404_for_missing(client):
    """English text id English text 404"""
    resp = client.get("/api/decision/not_exists_xxx")
    assert resp.status_code == 404


def test_decision_patch_returns_404_for_missing(client):
    """English text id English text 404"""
    resp = client.patch("/api/decision/not_exists_xxx", json={"executed": True})
    assert resp.status_code == 404


def test_decision_delete_returns_404_for_missing(client):
    """English text id English text 404"""
    resp = client.delete("/api/decision/not_exists_xxx")
    assert resp.status_code == 404


# ─── /api/archive ───────────────────────────────────────────


def test_archive_lists_chat_history(client):
    """POST /api/chat English text GET /api/archive English text"""
    # English text chatEnglish text
    resp = client.post("/api/chat", json={"question": "English text", "mode": "random"})
    assert resp.status_code == 200
    chat_decision_id = resp.json()["decisionId"]
    assert chat_decision_id

    # English text archive
    resp = client.get("/api/archive")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["total"] >= 1
    assert any(item["id"] == chat_decision_id for item in body["list"])


def test_archive_empty_when_no_decisions(client):
    """English text archive English text total=0"""
    resp = client.get("/api/archive")
    assert resp.status_code == 200
    body = resp.json()
    assert body["list"] == []
    assert body["total"] == 0


# ─── /api/stats ─────────────────────────────────────────────


def test_stats_returns_full_shape(client):
    """GET /api/stats English text totalDecisions/modeDistribution/avgConfidence/executedRate/regretRate/weekTrend"""
    # English text total > 0
    client.post("/api/chat", json={"question": "English text", "mode": "random"})
    client.post("/api/chat", json={"question": "English text", "mode": "rational"})

    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalDecisions"] >= 2
    # English text 6 English text
    assert set(body["modeDistribution"].keys()) == {
        "auto", "rational", "random", "nature", "dialogue", "fengshui"
    }
    # English text random English text
    assert body["modeDistribution"]["random"] >= 1
    assert isinstance(body["avgConfidence"], (int, float))
    assert 0.0 <= body["executedRate"] <= 1.0
    assert 0.0 <= body["regretRate"] <= 1.0
    # weekTrend English text 7 English text
    assert len(body["weekTrend"]) == 7
    for item in body["weekTrend"]:
        assert "date" in item and "count" in item


def test_stats_empty_returns_zeros(client):
    """English text stats English text 0"""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalDecisions"] == 0
    assert body["avgConfidence"] == 0.0
    assert body["executedRate"] == 0.0
    assert body["regretRate"] == 0.0
    assert len(body["weekTrend"]) == 7
    assert all(item["count"] == 0 for item in body["weekTrend"])


# ─── /api/preferences ───────────────────────────────────────


def test_preferences_get_returns_defaults(client):
    """GET /api/preferences English textEnglish text"""
    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    prefs = resp.json()
    assert prefs["language"] == "zh-CN"
    assert prefs["default_mode"] == "auto"


def test_preferences_post_persists(client):
    """POST /api/preferences English text GET English text"""
    resp = client.post("/api/preferences", json={"language": "yue", "theme": "dark", "skin": "console", "demo_mode": True})
    assert resp.status_code == 200
    saved = resp.json()
    assert saved["language"] == "yue"
    assert saved["theme"] == "dark"
    assert saved["skin"] == "console"
    assert saved["demo_mode"] is True

    # GET English text
    resp = client.get("/api/preferences")
    prefs = resp.json()
    assert prefs["language"] == "yue"
    assert prefs["theme"] == "dark"
    assert prefs["skin"] == "console"
    assert prefs["demo_mode"] is True
