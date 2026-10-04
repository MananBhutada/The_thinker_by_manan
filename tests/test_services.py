"""English text

English text
  - mode_recognizer: recognize / explain
  - bazi_engine: year_pillar / parse
  - decision_score: score
  - nature_signal: build
  - llm_service: English text mock / sanitize_result English text
"""

import pytest

from services.bazi_engine import parse, year_pillar
from services.decision_score import score
from services.llm_service import call_llm, sanitize_result
from services.mode_recognizer import explain, recognize
from services.nature_signal import build as build_nature_signal


# ─── mode_recognizer ────────────────────────────────────────


def test_mode_recognizer_lunch_question_returns_random():
    """recognize English textEnglish textEnglish text random"""
    assert recognize("English text") == "random"


def test_mode_recognizer_empty_returns_auto():
    """English text auto"""
    assert recognize("") == "auto"
    assert recognize(None) == "auto"  # type: ignore[arg-type]


def test_mode_recognizer_explain_returns_full_shape():
    """explain English text {mode, reason, confidence} English textconfidence English text"""
    result = explain("English text")
    assert set(result.keys()) >= {"mode", "reason", "confidence"}
    assert result["mode"] == "random"
    assert isinstance(result["reason"], str) and result["reason"]
    assert isinstance(result["confidence"], int)
    assert 0 <= result["confidence"] <= 100


def test_mode_recognizer_explain_unmatched_falls_back_to_rational():
    """English text rationalconfidence=52"""
    result = explain("hello world")
    assert result["mode"] == "rational"
    assert result["confidence"] == 52


def test_mode_recognizer_fengshui_keywords():
    """English text/English text fengshui"""
    assert recognize("English text") == "fengshui"
    assert recognize("English text") == "fengshui"


def test_mode_recognizer_dialogue_keywords():
    """English text/English text dialogue"""
    assert recognize("English textEnglish text") == "dialogue"


# ─── bazi_engine ────────────────────────────────────────────


def test_bazi_year_pillar_1990_is_gengwu():
    """1990English text6English text15English textEnglish textEnglish text English text"""
    yp = year_pillar(1990, 6, 15)
    assert "English text" in yp
    assert yp.endswith("English text")


def test_bazi_year_pillar_before_lichun_uses_previous_year():
    """1990English text1English text15English textEnglish textEnglish text 1989 English textEnglish text English text"""
    yp = year_pillar(1990, 1, 15)
    assert "English text" in yp


def test_bazi_year_pillar_1984_is_jiazi():
    """1984 English textEnglish text"""
    assert year_pillar(1984, 6, 15) == "English text"


def test_bazi_year_pillar_none_returns_placeholder():
    """year English text None English text"""
    assert year_pillar(None, None, None) == "English text"


def test_bazi_parse_extracts_year_month_day():
    """parse English text1990English text6English text15English textEnglish text year/month/day"""
    info = parse("1990English text6English text15English text")
    assert info["year"] == 1990
    assert info["month"] == 6
    assert info["day"] == 15


def test_bazi_parse_extracts_gender_and_hour():
    """parse English text"""
    info = parse("English text 1990English text6English text15English text English text English text English text")
    assert info["gender"] == "English text"
    assert info["hour"] is not None
    assert info["hour"]["branch"] == "English text"
    assert info["calendar"] == "English text"
    assert info["place"] == "English text"


def test_bazi_parse_missing_fields_returns_missing_list():
    """parse English text missing English text"""
    info = parse("English text")
    assert info["year"] is None
    assert info["month"] is None
    assert info["day"] is None
    assert "English text" in info["missing"]
    assert "English text" in info["missing"]
    assert "English text" in info["missing"]
    assert "English text" in info["missing"]


# ─── decision_score ─────────────────────────────────────────


def test_decision_score_returns_six_fields():
    """score() English text 6 English textbenefit/risk/cost/reversibility/valueFit/confidence"""
    result = score(
        "English text",
        {"pros": ["English text", "English text", "English text"], "cons": ["English text", "English text"]},
        {"efficiency": 70, "risk": 40, "growth": 80, "relationship": 50},
    )
    assert set(result.keys()) == {
        "benefit", "risk", "cost", "reversibility", "valueFit", "confidence"
    }
    # English text 0-100 English text
    for v in result.values():
        assert isinstance(v, int)
        assert 0 <= v <= 100


def test_decision_score_high_risk_question():
    """English textEnglish text/English textEnglish text risk=72"""
    result = score("English text", {"pros": [], "cons": []}, None)
    assert result["risk"] == 72
    # English textreversibility=46
    assert result["reversibility"] == 46


def test_decision_score_high_reversibility_question():
    """English textEnglish text/English textEnglish text reversibility=72"""
    result = score("English text", {"pros": [], "cons": []}, None)
    assert result["reversibility"] == 72
    assert result["risk"] == 42  # English text


def test_decision_score_handles_none_inputs():
    """None English textEnglish text fallback"""
    result = score("", None, None)
    assert result["benefit"] == 48  # 0 + 0 + 0 = 48
    assert result["cost"] == 38


# ─── nature_signal ──────────────────────────────────────────


def test_nature_signal_build_returns_weights_and_summary():
    """build() English text {weights, summary}weights English text"""
    weather = {
        "isReal": True,
        "weather": "English text",
        "wind": "English text 3 English text",
        "temperature": 22,
        "humidity": "65%",
        "air": "English text",
        "time": "English text",
        "season": "English text",
    }
    result = build_nature_signal(weather)
    assert "weights" in result
    assert "summary" in result
    assert isinstance(result["weights"], list) and len(result["weights"]) >= 3
    # English text 32
    assert result["weights"][0]["name"] == "English text"
    assert result["weights"][0]["weight"] == 32
    # summary English text
    assert "English text32%:English text" in result["summary"]


def test_nature_signal_build_handles_none():
    """weather=None English textEnglish text"""
    result = build_nature_signal(None)
    assert result["weights"][0]["name"] == "English text"
    assert result["weights"][0]["weight"] == 16
    # English text
    names = [w["name"] for w in result["weights"]]
    assert "English text" in names
    assert "English text" in names


def test_nature_signal_build_degraded_weather():
    """isReal=False English text 16"""
    result = build_nature_signal({"isReal": False, "weather": "English text"})
    assert result["weights"][0] == {"name": "English text", "weight": 16, "value": "English text"}


def test_nature_signal_uses_extended_reference_values():
    result = build_nature_signal({
        "isReal": True,
        "weather": "English text",
        "alarms": [{"title": "English text"}],
        "forecast_24h": [{"time": "English text", "weather": "English text", "temperature": 29}],
        "life_indices": [{"name": "English text", "text": "English text"}],
        "moonPhase": "English text",
        "time": "English text",
        "season": "English text",
    })
    names = [item["name"] for item in result["weights"]]
    assert "English text" in names
    assert "English text" in names
    assert "English text" in names
    assert "English text" in names


# ─── llm_service ────────────────────────────────────────────


def test_llm_service_call_llm_returns_mock_when_no_config(monkeypatch):
    """English text LLM English text call_llm English text _source=mock"""
    # conftest English text DBEnglish textEnglish text
    for env in ("CHOICE_LLM_API_KEY", "CHOICE_LLM_BASE_URL", "CHOICE_LLM_MODEL"):
        monkeypatch.delenv(env, raising=False)

    result = call_llm("English text", "rational", config={}, allow_mock=True)
    assert result["_source"] == "mock"
    assert result["type"] == "rational"
    # rational mock English text pros/cons/conclusion
    assert "pros" in result and len(result["pros"]) >= 1
    assert "cons" in result and len(result["cons"]) >= 1
    assert "conclusion" in result


def test_llm_service_call_llm_random_returns_six_options(monkeypatch):
    """random English text mock English text 6 English text"""
    for env in ("CHOICE_LLM_API_KEY", "CHOICE_LLM_BASE_URL", "CHOICE_LLM_MODEL"):
        monkeypatch.delenv(env, raising=False)

    result = call_llm("English text", "random", config={}, allow_mock=True)
    assert result["_source"] == "mock"
    assert result["type"] == "random"
    assert len(result["options"]) == 6


def test_llm_service_call_llm_fengshui_returns_need_birth(monkeypatch):
    """fengshui English text mock English text needBirth=True"""
    for env in ("CHOICE_LLM_API_KEY", "CHOICE_LLM_BASE_URL", "CHOICE_LLM_MODEL"):
        monkeypatch.delenv(env, raising=False)

    result = call_llm("English text", "fengshui", config={}, allow_mock=True)
    assert result["_source"] == "mock"
    assert result["type"] == "fengshui"
    assert result["needBirth"] is True


def test_llm_service_call_llm_rejects_nature_mode():
    """call_llm English text nature English textEnglish text nature_service"""
    with pytest.raises(ValueError):
        call_llm("test", "nature", config={})


def test_llm_service_sanitize_result_fills_missing_rational_fields():
    """sanitize_result English text pros/cons/conclusion English text fallback"""
    raw = {"type": "rational"}  # English text pros/cons/conclusion
    result = sanitize_result(raw, "rational")
    assert result["type"] == "rational"
    assert result["pros"]  # English text
    assert result["cons"]
    assert result["conclusion"]
    # English text schemaWarning
    assert result.get("_schemaWarning")


def test_llm_service_sanitize_result_fills_missing_random_options():
    """sanitize_result English text random English text 6 English text"""
    raw = {"type": "random"}  # English text options
    result = sanitize_result(raw, "random")
    assert result["type"] == "random"
    assert len(result["options"]) == 6


def test_llm_service_sanitize_result_fills_missing_dialogue_fields():
    """sanitize_result English text dialogue English text question English text 3 English text options"""
    raw = {"type": "dialogue"}
    result = sanitize_result(raw, "dialogue")
    assert result["type"] == "dialogue"
    assert result["question"]
    assert len(result["options"]) >= 3


def test_llm_service_sanitize_result_handles_non_dict():
    """sanitize_result English text dict English text _schemaWarning English text"""
    result = sanitize_result("not a dict", "rational")  # type: ignore[arg-type]
    assert result["type"] == "rational"
    assert "_schemaWarning" in result
