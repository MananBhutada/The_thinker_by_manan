"""SQLite English text

English text HTML English text IndexedDBEnglish text decisions English text config English text
English text SQLiteEnglish textEnglish text

English text
  - decisions: English textid/question/mode/result/brief/createdAt/executed/regret/dialogueHistory
  - config: English textkey/valueEnglish text LLM/English text API Key English text
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# SQLite English textEnglish text backend/ English textgitignore English text *.db
DB_PATH = Path(__file__).parent / "choice.db"


def get_conn() -> sqlite3.Connection:
    """English text SQLite English textEnglish textEnglish text"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """English textEnglish text"""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                mode TEXT NOT NULL,
                result TEXT NOT NULL,
                brief TEXT,
                created_at TEXT NOT NULL,
                executed INTEGER DEFAULT 0,
                regret INTEGER DEFAULT 0,
                dialogue_history TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);
            CREATE INDEX IF NOT EXISTS idx_decisions_mode ON decisions(mode);

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )


# ─── decisions English text ───────────────────────────────────────────


def save_decision(dec: dict) -> dict:
    """English text/English textEnglish text decEnglish text"""
    if not dec.get("id"):
        dec["id"] = f"dec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{_random_suffix()}"
    if not dec.get("createdAt"):
        dec["createdAt"] = datetime.now().isoformat()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO decisions
                (id, question, mode, result, brief, created_at, executed, regret, dialogue_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dec["id"],
                dec["question"],
                dec["mode"],
                json.dumps(dec.get("result", {}), ensure_ascii=False),
                json.dumps(dec.get("brief"), ensure_ascii=False) if dec.get("brief") else None,
                dec["createdAt"],
                1 if dec.get("executed") else 0,
                1 if dec.get("regret") else 0,
                json.dumps(dec.get("dialogueHistory"), ensure_ascii=False) if dec.get("dialogueHistory") else None,
            ),
        )
    return dec


def get_decision(decision_id: str) -> Optional[dict]:
    """English text id English text"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    return _row_to_decision(row) if row else None


def list_decisions(limit: int = 100, offset: int = 0) -> list[dict]:
    """English textEnglish text createdAt English text"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [_row_to_decision(r) for r in rows]


def update_decision(decision_id: str, patches: dict) -> Optional[dict]:
    """English textEnglish text executed/regret/dialogueHistory English text"""
    allowed = {"executed", "regret", "dialogueHistory"}
    updates = {k: v for k, v in patches.items() if k in allowed}
    if not updates:
        return get_decision(decision_id)

    sets = []
    vals = []
    if "executed" in updates:
        sets.append("executed = ?")
        vals.append(1 if updates["executed"] else 0)
    if "regret" in updates:
        sets.append("regret = ?")
        vals.append(1 if updates["regret"] else 0)
    if "dialogueHistory" in updates:
        sets.append("dialogue_history = ?")
        vals.append(json.dumps(updates["dialogueHistory"], ensure_ascii=False))

    vals.append(decision_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE decisions SET {', '.join(sets)} WHERE id = ?", vals)
    return get_decision(decision_id)


def delete_decision(decision_id: str) -> bool:
    """English textEnglish text"""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM decisions WHERE id = ?", (decision_id,))
        return cur.rowcount > 0


def count_decisions() -> int:
    """English text"""
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM decisions").fetchone()
    return row["n"]


# ─── config English text ──────────────────────────────────────────────


def get_config_value(key: str, default: Any = None) -> Any:
    """English text"""
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return default


def set_config_value(key: str, value: Any) -> None:
    """English textupsert"""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, json.dumps(value, ensure_ascii=False)),
        )


def get_all_config() -> dict:
    """English textEnglish text {key: value} English text"""
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM config").fetchall()
    out = {}
    for r in rows:
        try:
            out[r["key"]] = json.loads(r["value"])
        except (json.JSONDecodeError, TypeError):
            out[r["key"]] = r["value"]
    return out


def delete_config_value(key: str) -> None:
    """English text"""
    with get_conn() as conn:
        conn.execute("DELETE FROM config WHERE key = ?", (key,))


# ─── English text ───────────────────────────────────────────────────


def _row_to_decision(row: sqlite3.Row) -> dict:
    """English text Decision dict"""
    out = {
        "id": row["id"],
        "question": row["question"],
        "mode": row["mode"],
        "result": json.loads(row["result"]) if row["result"] else {},
        "createdAt": row["created_at"],
        "executed": bool(row["executed"]),
        "regret": bool(row["regret"]),
    }
    if row["brief"]:
        out["brief"] = json.loads(row["brief"])
    if row["dialogue_history"]:
        out["dialogueHistory"] = json.loads(row["dialogue_history"])
    return out


def _random_suffix() -> str:
    """6 English textbase36"""
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
