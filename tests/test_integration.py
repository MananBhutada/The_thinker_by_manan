"""English text6 English text + English text + English text

English textEnglish text http://localhost:8765English text HTTP English text
English text TestClientEnglish text
1. 6 English textauto/rational/random/nature/dialogue/fengshuiEnglish text /api/chat English text
2. English textPOST /api/config → GET English text → DELETE English text
3. English textchat English text → archive English text → decision English text/English text → stats English text
4. preferences GET/POST
"""

import os
import sys
from pathlib import Path

import httpx
import pytest

# English text backend English text sys.path English text schemas
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

BASE_URL = os.environ.get("CHOICE_TEST_BASE_URL", "http://localhost:8765")


@pytest.fixture(scope="module")
def client():
    """HTTP English text"""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        # English text
        try:
            r = c.get("/api/health")
            r.raise_for_status()
        except Exception as e:
            pytest.skip(f"English text {BASE_URL}{e}")
        yield c


# ============================== 1. English text ==============================

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["name"]
    assert data["version"]


def test_modes(client):
    r = client.get("/api/modes")
    assert r.status_code == 200
    data = r.json()
    # English text {modes: [...], quickQuestions: [...]}
    assert "modes" in data
    assert "quickQuestions" in data
    modes = data["modes"]
    assert isinstance(modes, list)
    assert len(modes) == 6
    ids = {m["id"] for m in modes}
    assert ids == {"auto", "rational", "random", "nature", "dialogue", "fengshui"}
    assert isinstance(data["quickQuestions"], list)
    assert len(data["quickQuestions"]) >= 1


# ============================== 2. 6 English text ==============================

def test_chat_auto(client):
    r = client.post("/api/chat", json={"question": "English text", "mode": "auto"})
    assert r.status_code == 200
    d = r.json()
    # auto English text mode English textEnglish text 'auto'
    assert d["mode"] in {"rational", "random", "nature", "dialogue", "fengshui"}
    assert d["autoRecognized"] is not None
    assert d["autoRecognized"]["mode"] == d["mode"]
    assert d["reply"]
    assert d["result"] is not None
    assert d["decisionId"]


def test_chat_rational(client):
    r = client.post("/api/chat", json={"question": "English text", "mode": "rational"})
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "rational"
    assert d["reply"]
    assert d["result"] is not None
    # rational English text conclusion English text pros/cons
    res = d["result"]
    assert "conclusion" in res or "pros" in res or "score" in res
    assert d["decisionId"]


def test_chat_random(client):
    r = client.post("/api/chat", json={"question": "English text", "mode": "random"})
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "random"
    assert d["reply"]
    res = d["result"]
    # random English text options English text wheelResult
    assert "options" in res or "wheelResult" in res
    assert d["decisionId"]


def test_chat_nature(client):
    r = client.post("/api/chat", json={"question": "English text", "mode": "nature"})
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "nature"
    assert d["reply"]
    # nature English text nature English text
    assert d["nature"] is not None
    n = d["nature"]
    assert "signal" in n or "suggestion" in n
    assert d["decisionId"]


def test_chat_dialogue(client):
    r = client.post("/api/chat", json={"question": "English text", "mode": "dialogue"})
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "dialogue"
    assert d["reply"]
    res = d["result"]
    # dialogue English text optionsEnglish textEnglish text needBirth/question
    assert "options" in res or "question" in res or "needBirth" in res
    assert d["decisionId"]


def test_chat_fengshui(client):
    r = client.post("/api/chat", json={"question": "English text", "mode": "fengshui"})
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "fengshui"
    assert d["reply"]
    res = d["result"]
    # fengshui English text bazi / baziAudit / needBirth
    assert "bazi" in res or "baziAudit" in res or "needBirth" in res
    assert d["decisionId"]


# ============================== 3. English text ==============================

def test_config_flow(client):
    # 1. English text GET English textEnglish text
    r = client.get("/api/config")
    assert r.status_code == 200
    before = r.json()
    assert "llm" in before
    assert "weather" in before
    assert "hasLlm" in before
    assert "hasWeather" in before
    # English textEnglish text key
    assert "apiKey" not in before["llm"]
    assert before["llm"].get("hasKey") in (True, False)

    # 2. POST English text modelEnglish text api_key English text
    r = client.post("/api/config", json={"llm_model": "test-model-integration"})
    assert r.status_code == 200
    saved = r.json()
    assert saved["llm"]["model"] == "test-model-integration"

    # 3. GET English text
    r = client.get("/api/config")
    assert r.status_code == 200
    after = r.json()
    assert after["llm"]["model"] == "test-model-integration"

    # 4. POST English text LLM keyEnglish text
    r = client.post("/api/config", json={
        "llm_api_key": "sk-test-integration-key",
        "llm_base_url": "https://api.test.com/v1",
    })
    assert r.status_code == 200
    assert r.json()["llm"]["hasKey"] is True

    # 5. GET English text hasKey English text TrueEnglish text key
    r = client.get("/api/config")
    data = r.json()
    assert data["llm"]["hasKey"] is True
    assert "sk-test-integration-key" not in r.text  # English text

    # 6. DELETE English text
    r = client.delete("/api/config")
    assert r.status_code == 200

    # 7. GET English text
    r = client.get("/api/config")
    data = r.json()
    assert data["llm"]["hasKey"] is False
    assert data["weather"]["hasAppid"] is False


# ============================== 4. English text ==============================

def test_persistence_flow(client):
    # 1. English text chatEnglish text decisionId
    r = client.post("/api/chat", json={"question": "English text", "mode": "random"})
    assert r.status_code == 200
    did = r.json()["decisionId"]
    assert did

    # 2. GET /api/decision/{id} English text
    r = client.get(f"/api/decision/{did}")
    assert r.status_code == 200
    d = r.json()
    assert d["id"] == did
    assert d["question"] == "English text"
    assert d["mode"] == "random"
    assert d["result"] is not None

    # 3. PATCH English text executed
    r = client.patch(f"/api/decision/{did}", json={"executed": True})
    assert r.status_code == 200
    assert r.json()["executed"] is True

    # 4. PATCH English text regret
    r = client.patch(f"/api/decision/{did}", json={"regret": True})
    assert r.status_code == 200
    assert r.json()["regret"] is True

    # 5. GET /api/archive English text
    r = client.get("/api/archive")
    assert r.status_code == 200
    arc = r.json()
    assert arc["ok"] is True
    assert "list" in arc
    assert "total" in arc
    ids = [item["id"] for item in arc["list"]]
    assert did in ids

    # 6. GET /api/stats English text
    r = client.get("/api/stats")
    assert r.status_code == 200
    s = r.json()
    assert s["totalDecisions"] >= 1
    assert "modeDistribution" in s
    assert "executedRate" in s
    assert "regretRate" in s
    assert "weekTrend" in s
    # random English text 1 English text
    assert s["modeDistribution"].get("random", 0) >= 1

    # 7. DELETE /api/decision/{id}
    r = client.delete(f"/api/decision/{did}")
    assert r.status_code == 200

    # 8. GET English text 404
    r = client.get(f"/api/decision/{did}")
    assert r.status_code == 404


# ============================== 5. preferences ==============================

def test_preferences_flow(client):
    # 1. GET English textEnglish text
    r = client.get("/api/preferences")
    assert r.status_code == 200
    before = r.json()
    assert "default_mode" in before or "language" in before  # English text

    # 2. POST English text default_mode / theme / language
    r = client.post("/api/preferences", json={
        "default_mode": "rational",
        "theme": "dark",
        "language": "zh-CN",
    })
    assert r.status_code == 200
    saved = r.json()
    assert saved.get("default_mode") == "rational"
    assert saved.get("theme") == "dark"
    assert saved.get("language") == "zh-CN"

    # 3. GET English text
    r = client.get("/api/preferences")
    assert r.status_code == 200
    after = r.json()
    assert after.get("default_mode") == "rational"
    assert after.get("theme") == "dark"
    assert after.get("language") == "zh-CN"

    # 4. English textEnglish text
    client.post("/api/preferences", json={
        "default_mode": before.get("default_mode", "auto"),
        "theme": before.get("theme", "auto"),
        "language": before.get("language", "zh-CN"),
    })


# ============================== 6. archive English text ==============================

def test_archive_pagination(client):
    r = client.get("/api/archive?page=1&pageSize=5")
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["page"] == 1
    assert d["pageSize"] == 5
    assert isinstance(d["list"], list)
    assert len(d["list"]) <= 5


# ============================== 7. English text ==============================

def test_chat_missing_question(client):
    r = client.post("/api/chat", json={"mode": "auto"})
    assert r.status_code == 422  # Pydantic English text


def test_chat_invalid_mode(client):
    r = client.post("/api/chat", json={"question": "x", "mode": "invalid"})
    assert r.status_code == 422


def test_decision_not_found(client):
    r = client.get("/api/decision/nonexistent-id-xxx")
    assert r.status_code == 404
