"""PostgreSQL persistence for FounderOS.

The application uses PostgreSQL as the only runtime database. Every persisted
record is scoped to the request's workspace_id so the later authentication layer
can map users to workspaces without redesigning the storage boundary.

Graph documents remain JSONB for now. This keeps the current graph API stable
while giving us PostgreSQL durability, indexing, transactions, backups and a
clean path toward normalized FounderOS entities later.
"""

import contextvars
import json
import os
import random
import string
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. FounderOS now uses PostgreSQL; "
        "configure a PostgreSQL connection string before starting the API."
    )

_workspace_id = contextvars.ContextVar("founderos_workspace_id", default="local")


def set_workspace_id(workspace_id: str):
    return _workspace_id.set(workspace_id or "local")


def reset_workspace_id(token):
    _workspace_id.reset(token)


def current_workspace_id() -> str:
    return _workspace_id.get()


def get_conn():
    """Return a PostgreSQL connection with dictionary-shaped rows."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def _ensure_workspace(conn, workspace_id: Optional[str] = None) -> str:
    workspace_id = workspace_id or current_workspace_id()
    conn.execute(
        """
        INSERT INTO founder_workspaces (workspace_id, data, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (workspace_id) DO NOTHING
        """,
        (workspace_id, Jsonb(_empty_graph()), datetime.now(timezone.utc)),
    )
    return workspace_id


def init_db() -> None:
    """Create the PostgreSQL schema if it does not already exist."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS founder_workspaces (
                workspace_id TEXT PRIMARY KEY,
                data JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_founder_workspaces_updated_at
                ON founder_workspaces(updated_at);

            CREATE TABLE IF NOT EXISTS decisions (
                workspace_id TEXT NOT NULL REFERENCES founder_workspaces(workspace_id) ON DELETE CASCADE,
                id TEXT NOT NULL,
                question TEXT NOT NULL,
                mode TEXT NOT NULL,
                result JSONB NOT NULL DEFAULT '{}'::jsonb,
                brief JSONB,
                created_at TIMESTAMPTZ NOT NULL,
                executed BOOLEAN NOT NULL DEFAULT FALSE,
                regret BOOLEAN NOT NULL DEFAULT FALSE,
                dialogue_history JSONB,
                PRIMARY KEY (workspace_id, id)
            );

            CREATE INDEX IF NOT EXISTS idx_decisions_workspace_created_at
                ON decisions(workspace_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_decisions_workspace_mode
                ON decisions(workspace_id, mode);

            CREATE TABLE IF NOT EXISTS config (
                workspace_id TEXT NOT NULL REFERENCES founder_workspaces(workspace_id) ON DELETE CASCADE,
                key TEXT NOT NULL,
                value JSONB NOT NULL,
                PRIMARY KEY (workspace_id, key)
            );

            CREATE TABLE IF NOT EXISTS graph_state (
                workspace_id TEXT PRIMARY KEY REFERENCES founder_workspaces(workspace_id) ON DELETE CASCADE,
                data JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


def save_decision(dec: dict) -> dict:
    if not dec.get("id"):
        dec["id"] = f"dec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{_random_suffix()}"
    if not dec.get("createdAt"):
        dec["createdAt"] = datetime.now(timezone.utc).isoformat()

    workspace_id = current_workspace_id()
    created_at = _parse_timestamp(dec["createdAt"])

    with get_conn() as conn:
        _ensure_workspace(conn, workspace_id)
        conn.execute(
            """
            INSERT INTO decisions
                (workspace_id, id, question, mode, result, brief, created_at,
                 executed, regret, dialogue_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id, id) DO UPDATE SET
                question = EXCLUDED.question,
                mode = EXCLUDED.mode,
                result = EXCLUDED.result,
                brief = EXCLUDED.brief,
                created_at = EXCLUDED.created_at,
                executed = EXCLUDED.executed,
                regret = EXCLUDED.regret,
                dialogue_history = EXCLUDED.dialogue_history
            """,
            (
                workspace_id,
                dec["id"],
                dec["question"],
                dec["mode"],
                Jsonb(dec.get("result", {})),
                Jsonb(dec["brief"]) if dec.get("brief") else None,
                created_at,
                bool(dec.get("executed")),
                bool(dec.get("regret")),
                Jsonb(dec["dialogueHistory"]) if dec.get("dialogueHistory") else None,
            ),
        )
    return dec


def get_decision(decision_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM decisions
            WHERE workspace_id = %s AND id = %s
            """,
            (current_workspace_id(), decision_id),
        ).fetchone()
    return _row_to_decision(row) if row else None


def list_decisions(limit: int = 100, offset: int = 0) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM decisions
            WHERE workspace_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (current_workspace_id(), limit, offset),
        ).fetchall()
    return [_row_to_decision(r) for r in rows]


def update_decision(decision_id: str, patches: dict) -> Optional[dict]:
    allowed = {"executed", "regret", "dialogueHistory"}
    updates = {k: v for k, v in patches.items() if k in allowed}
    if not updates:
        return get_decision(decision_id)

    assignments = []
    values = []
    if "executed" in updates:
        assignments.append("executed = %s")
        values.append(bool(updates["executed"]))
    if "regret" in updates:
        assignments.append("regret = %s")
        values.append(bool(updates["regret"]))
    if "dialogueHistory" in updates:
        assignments.append("dialogue_history = %s")
        values.append(Jsonb(updates["dialogueHistory"]))

    values.extend([current_workspace_id(), decision_id])
    with get_conn() as conn:
        conn.execute(
            f"""
            UPDATE decisions
            SET {", ".join(assignments)}
            WHERE workspace_id = %s AND id = %s
            """,
            values,
        )
    return get_decision(decision_id)


def delete_decision(decision_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM decisions WHERE workspace_id = %s AND id = %s",
            (current_workspace_id(), decision_id),
        )
        return cur.rowcount > 0


def count_decisions() -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM decisions WHERE workspace_id = %s",
            (current_workspace_id(),),
        ).fetchone()
    return int(row["n"])


# ---------------------------------------------------------------------------
# Per-workspace config
# ---------------------------------------------------------------------------


def get_config_value(key: str, default: Any = None) -> Any:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT value FROM config
            WHERE workspace_id = %s AND key = %s
            """,
            (current_workspace_id(), key),
        ).fetchone()
    if not row:
        return default
    value = row["value"]
    return value if value is not None else default


def set_config_value(key: str, value: Any) -> None:
    workspace_id = current_workspace_id()
    with get_conn() as conn:
        _ensure_workspace(conn, workspace_id)
        conn.execute(
            """
            INSERT INTO config (workspace_id, key, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (workspace_id, key) DO UPDATE SET
                value = EXCLUDED.value
            """,
            (workspace_id, key, Jsonb(value)),
        )


def get_all_config() -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT key, value FROM config
            WHERE workspace_id = %s
            """,
            (current_workspace_id(),),
        ).fetchall()
    return {row["key"]: row["value"] for row in rows}


def delete_config_value(key: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM config WHERE workspace_id = %s AND key = %s",
            (current_workspace_id(), key),
        )


# ---------------------------------------------------------------------------
# Graph document
# ---------------------------------------------------------------------------


def _row_to_decision(row: dict) -> dict:
    out = {
        "id": row["id"],
        "question": row["question"],
        "mode": row["mode"],
        "result": row["result"] or {},
        "createdAt": _timestamp_to_iso(row["created_at"]),
        "executed": bool(row["executed"]),
        "regret": bool(row["regret"]),
    }
    if row["brief"] is not None:
        out["brief"] = row["brief"]
    if row["dialogue_history"] is not None:
        out["dialogueHistory"] = row["dialogue_history"]
    return out


def _random_suffix() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _timestamp_to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _empty_graph() -> dict:
    return {
        "root": {"title": "Your Startup", "summary": ""},
        "nodes": [],
        "edges": [],
        "insights": [],
        "questions": [],
    }


def save_graph(graph: dict) -> dict:
    workspace_id = current_workspace_id()
    now = datetime.now(timezone.utc)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO founder_workspaces (workspace_id, data, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (workspace_id) DO UPDATE SET
                data = EXCLUDED.data,
                updated_at = EXCLUDED.updated_at
            """,
            (workspace_id, Jsonb(graph), now),
        )
    return graph


def get_graph() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT data FROM founder_workspaces
            WHERE workspace_id = %s
            """,
            (current_workspace_id(),),
        ).fetchone()

    if not row:
        return _empty_graph()

    raw = row["data"]
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return _empty_graph()


def healthcheck() -> None:
    """Raise if the PostgreSQL datastore is unreachable."""
    with get_conn() as conn:
        conn.execute("SELECT 1")
