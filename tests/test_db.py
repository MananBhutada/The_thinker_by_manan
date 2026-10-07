"""English textdb.pyEnglish text

English text
  - init_db English text decisions / config English text
  - save/get/list/update/delete/count English text
  - config English text CRUD
"""

import db


def _make_decision(question: str = "English text", mode: str = "random", **overrides) -> dict:
    """English text dictEnglish text"""
    payload = {
        "question": question,
        "mode": mode,
        "result": {"type": mode, "options": ["A", "B"]},
        "executed": False,
        "regret": False,
    }
    payload.update(overrides)
    return payload


def test_init_db_creates_core_postgres_tables():
    """The PostgreSQL schema contains the core FounderOS tables."""
    with db.get_conn() as conn:
        tables = {
            row["table_name"]
            for row in conn.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            ).fetchall()
        }
    assert {"founder_workspaces", "decisions", "config"} <= tables


def test_save_and_get_decision():
    """save English text id English textEnglish text"""
    saved = db.save_decision(_make_decision(question="English text", mode="rational"))
    assert saved["id"]
    assert saved["createdAt"]

    fetched = db.get_decision(saved["id"])
    assert fetched is not None
    assert fetched["question"] == "English text"
    assert fetched["mode"] == "rational"
    assert fetched["result"] == {"type": "rational", "options": ["A", "B"]}
    assert fetched["executed"] is False
    assert fetched["regret"] is False


def test_get_decision_returns_none_for_missing_id():
    """English text id English text None"""
    assert db.get_decision("not_exists_id_123") is None


def test_list_decisions_sorted_by_created_at_desc():
    """English text createdAt English textEnglish text"""
    import time

    # English textEnglish text createdAt English text
    older = db.save_decision(_make_decision(question="English text", createdAt="2024-01-01T00:00:00"))
    middle = db.save_decision(_make_decision(question="English text", createdAt="2024-06-01T00:00:00"))
    newer = db.save_decision(_make_decision(question="English text", createdAt="2025-01-01T00:00:00"))

    items = db.list_decisions(limit=100, offset=0)
    # English text
    assert items[0]["id"] == newer["id"]
    assert items[1]["id"] == middle["id"]
    assert items[2]["id"] == older["id"]


def test_update_decision_patches_allowed_fields():
    """PATCH English text executed/regret/dialogueHistoryEnglish text"""
    saved = db.save_decision(_make_decision(question="English text", mode="rational"))
    updated = db.update_decision(
        saved["id"],
        {
            "executed": True,
            "regret": True,
            "dialogueHistory": [{"role": "user", "text": "English text"}],
            # English text questionEnglish text
            "question": "English text",
        },
    )
    assert updated is not None
    assert updated["executed"] is True
    assert updated["regret"] is True
    assert updated["dialogueHistory"] == [{"role": "user", "text": "English text"}]
    # question English text
    assert updated["question"] == "English text"


def test_update_decision_returns_none_for_missing_id():
    """English text id English text None"""
    assert db.update_decision("missing_id_xxx", {"executed": True}) is None


def test_delete_decision():
    """English text get English text NoneEnglish text False"""
    saved = db.save_decision(_make_decision(question="English text"))
    assert db.delete_decision(saved["id"]) is True
    assert db.get_decision(saved["id"]) is None
    # English text False
    assert db.delete_decision(saved["id"]) is False


def test_count_decisions():
    """English text"""
    assert db.count_decisions() == 0
    db.save_decision(_make_decision(question="English text1"))
    assert db.count_decisions() == 1
    db.save_decision(_make_decision(question="English text2"))
    db.save_decision(_make_decision(question="English text3"))
    assert db.count_decisions() == 3


def test_config_crud():
    """config English text set/get/get_all/delete English text"""
    # English text get English text
    assert db.get_config_value("llm_api_key", default="") == ""

    # set English text get English text
    db.set_config_value("llm_api_key", "sk-test-xxx")
    assert db.get_config_value("llm_api_key") == "sk-test-xxx"

    # English text dict English text
    db.set_config_value("preferences", {"language": "zh-CN", "theme": "dark"})
    assert db.get_config_value("preferences") == {"language": "zh-CN", "theme": "dark"}

    # get_all English text
    all_cfg = db.get_all_config()
    assert all_cfg["llm_api_key"] == "sk-test-xxx"
    assert all_cfg["preferences"]["language"] == "zh-CN"

    # delete English text get English text
    db.delete_config_value("llm_api_key")
    assert db.get_config_value("llm_api_key", default="<deleted>") == "<deleted>"


def test_workspace_data_is_isolated():
    """Graph, config and decisions cannot cross workspace boundaries."""
    first = db.set_workspace_id("workspace_alpha")
    try:
        db.save_graph({
            "root": {"title": "Alpha Startup", "summary": ""},
            "nodes": [],
            "edges": [],
            "insights": [],
            "questions": [],
        })
        db.set_config_value("llm_api_key", "alpha-secret")
        db.save_decision(_make_decision(question="alpha-only"))
    finally:
        db.reset_workspace_id(first)

    second = db.set_workspace_id("workspace_beta")
    try:
        assert db.get_graph()["root"]["title"] == "Your Startup"
        assert db.get_config_value("llm_api_key") is None
        assert db.count_decisions() == 0
    finally:
        db.reset_workspace_id(second)
