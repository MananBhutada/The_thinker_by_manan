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


def _upgrade_legacy_postgres_schema(conn) -> None:
    """Upgrade the earlier optional-Postgres schema in place."""
    columns = conn.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'founder_workspaces'
        """
    ).fetchall()
    column_types = {row["column_name"]: row["data_type"] for row in columns}

    if column_types.get("data") == "text":
        conn.execute(
            """
            ALTER TABLE founder_workspaces
            ALTER COLUMN data TYPE JSONB USING data::jsonb
            """
        )

    if column_types.get("updated_at") == "text":
        conn.execute(
            """
            ALTER TABLE founder_workspaces
            ALTER COLUMN updated_at TYPE TIMESTAMPTZ
            USING updated_at::timestamptz
            """
        )


def init_db() -> None:
    """Create or upgrade the PostgreSQL schema."""
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


            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(expires_at);

            CREATE TABLE IF NOT EXISTS workspaces (
                workspace_id TEXT PRIMARY KEY REFERENCES founder_workspaces(workspace_id) ON DELETE CASCADE,
                startup_title TEXT NOT NULL DEFAULT 'Your Startup',
                summary TEXT NOT NULL DEFAULT '',
                objective TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS domains (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                type TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                x DOUBLE PRECISION NOT NULL DEFAULT 0,
                y DOUBLE PRECISION NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_domains_workspace ON domains(workspace_id);

            CREATE TABLE IF NOT EXISTS subnodes (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                domain_id TEXT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                type TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                x DOUBLE PRECISION NOT NULL DEFAULT 0,
                y DOUBLE PRECISION NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_subnodes_workspace_domain ON subnodes(workspace_id, domain_id);

            CREATE TABLE IF NOT EXISTS thoughts (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                subnode_id TEXT NOT NULL REFERENCES subnodes(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'idea',
                source TEXT NOT NULL DEFAULT 'founder',
                archived BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            );
            CREATE INDEX IF NOT EXISTS idx_thoughts_workspace_subnode_created
                ON thoughts(workspace_id, subnode_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS graph_edges (
                id BIGSERIAL PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'semantic',
                relationship TEXT,
                confidence INTEGER,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                UNIQUE(workspace_id, source_id, target_id, kind)
            );
            CREATE INDEX IF NOT EXISTS idx_graph_edges_workspace ON graph_edges(workspace_id);

            CREATE TABLE IF NOT EXISTS workspace_state (
                workspace_id TEXT PRIMARY KEY REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                data JSONB NOT NULL DEFAULT '{}'::jsonb,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                context_node_id TEXT,
                title TEXT NOT NULL DEFAULT 'Founder Coach',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_workspace_updated
                ON chat_sessions(workspace_id, updated_at DESC);

            CREATE TABLE IF NOT EXISTS chat_messages (
                id BIGSERIAL PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                session_id TEXT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            );
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
                ON chat_messages(session_id, created_at ASC);

            CREATE TABLE IF NOT EXISTS ai_proposals (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
                node_id TEXT,
                proposal JSONB NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                resolved_at TIMESTAMPTZ
            );
            CREATE INDEX IF NOT EXISTS idx_ai_proposals_workspace_status
                ON ai_proposals(workspace_id, status);

            CREATE TABLE IF NOT EXISTS graph_state (
                workspace_id TEXT PRIMARY KEY REFERENCES founder_workspaces(workspace_id) ON DELETE CASCADE,
                data JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
        _upgrade_legacy_postgres_schema(conn)
        conn.execute("ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS owner_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_user_id)")

        # Backfill normalized workspace rows from any legacy JSONB graph documents.
        legacy_rows = conn.execute("SELECT workspace_id, data, updated_at FROM founder_workspaces").fetchall()
        for legacy in legacy_rows:
            exists = conn.execute("SELECT 1 FROM workspaces WHERE workspace_id = %s", (legacy["workspace_id"],)).fetchone()
            if not exists and isinstance(legacy["data"], dict):
                _sync_structured_workspace(conn, legacy["workspace_id"], legacy["data"], legacy["updated_at"] or datetime.now(timezone.utc))


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


def _sync_structured_workspace(conn, workspace_id: str, graph: dict, now: datetime) -> None:
    """Materialize the graph document into normalized FounderOS tables."""
    root = graph.get("root") or {}
    conn.execute(
        """
        INSERT INTO workspaces (workspace_id, startup_title, summary, objective, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (workspace_id) DO UPDATE SET
            startup_title = EXCLUDED.startup_title,
            summary = EXCLUDED.summary,
            objective = EXCLUDED.objective,
            updated_at = EXCLUDED.updated_at
        """,
        (
            workspace_id,
            str(root.get("title") or "Your Startup"),
            str(root.get("summary") or ""),
            str(root.get("objective") or ""),
            now,
        ),
    )

    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    domains = [n for n in nodes if n.get("level") == "domain"]
    subnodes = [n for n in nodes if n.get("level") == "subnode"]
    valid_domain_ids = {str(n.get("id")) for n in domains if n.get("id")}
    valid_subnode_ids = {str(n.get("id")) for n in subnodes if n.get("id")}

    conn.execute("DELETE FROM thoughts WHERE workspace_id = %s", (workspace_id,))
    conn.execute("DELETE FROM subnodes WHERE workspace_id = %s", (workspace_id,))
    conn.execute("DELETE FROM domains WHERE workspace_id = %s", (workspace_id,))
    conn.execute("DELETE FROM graph_edges WHERE workspace_id = %s", (workspace_id,))

    for n in domains:
        conn.execute(
            """
            INSERT INTO domains
                (id, workspace_id, title, type, metadata, x, y, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                n["id"], workspace_id, n.get("title") or "Untitled domain",
                n.get("type"), Jsonb({k: v for k, v in n.items() if k not in {"id","title","type","level","x","y"}}),
                float(n.get("x") or 0), float(n.get("y") or 0), now,
            ),
        )

    for n in subnodes:
        parent_id = next(
            (e.get("source") for e in (graph.get("edges") or [])
             if e.get("kind") == "structural" and e.get("target") == n.get("id")
             and e.get("source") in valid_domain_ids),
            None,
        )
        if not parent_id:
            continue
        conn.execute(
            """
            INSERT INTO subnodes
                (id, workspace_id, domain_id, title, type, metadata, x, y, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                n["id"], workspace_id, parent_id, n.get("title") or "Untitled sub-node",
                n.get("type"), Jsonb({k: v for k, v in n.items() if k not in {"id","title","type","level","domain","thoughts","x","y"}}),
                float(n.get("x") or 0), float(n.get("y") or 0), now,
            ),
        )
        for t in n.get("thoughts") or []:
            if not t.get("id") or not t.get("content"):
                continue
            conn.execute(
                """
                INSERT INTO thoughts
                    (id, workspace_id, subnode_id, content, type, source, archived, created_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    t["id"], workspace_id, n["id"], str(t.get("content") or ""),
                    str(t.get("type") or "idea"), str(t.get("source") or "founder"),
                    bool(t.get("archived")), _parse_timestamp(t.get("createdAt") or now),
                    Jsonb({k: v for k, v in t.items() if k not in {"id","content","type","source","archived","createdAt"}}),
                ),
            )

    valid_ids = valid_domain_ids | valid_subnode_ids | {"root"}
    for e in graph.get("edges") or []:
        if not e.get("source") or not e.get("target"):
            continue
        if e.get("source") not in valid_ids or e.get("target") not in valid_ids:
            continue
        conn.execute(
            """
            INSERT INTO graph_edges
                (workspace_id, source_id, target_id, kind, relationship, confidence, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id, source_id, target_id, kind) DO UPDATE SET
                relationship = EXCLUDED.relationship,
                confidence = EXCLUDED.confidence,
                metadata = EXCLUDED.metadata
            """,
            (
                workspace_id, e["source"], e["target"], str(e.get("kind") or "semantic"),
                e.get("relationship"), e.get("confidence"),
                Jsonb({k: v for k, v in e.items() if k not in {"source","target","kind","relationship","confidence"}}),
            ),
        )

    conn.execute(
        """
        INSERT INTO workspace_state (workspace_id, data, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (workspace_id) DO UPDATE SET
            data = EXCLUDED.data,
            updated_at = EXCLUDED.updated_at
        """,
        (
            workspace_id,
            Jsonb({
                "insights": graph.get("insights") or [],
                "questions": graph.get("questions") or [],
            }),
            now,
        ),
    )


def _load_structured_graph(conn, workspace_id: str) -> Optional[dict]:
    workspace = conn.execute(
        "SELECT startup_title, summary, objective FROM workspaces WHERE workspace_id = %s",
        (workspace_id,),
    ).fetchone()
    if not workspace:
        return None

    domain_rows = conn.execute(
        "SELECT * FROM domains WHERE workspace_id = %s ORDER BY created_at ASC, id ASC",
        (workspace_id,),
    ).fetchall()
    sub_rows = conn.execute(
        "SELECT * FROM subnodes WHERE workspace_id = %s ORDER BY created_at ASC, id ASC",
        (workspace_id,),
    ).fetchall()
    thought_rows = conn.execute(
        "SELECT * FROM thoughts WHERE workspace_id = %s ORDER BY created_at ASC, id ASC",
        (workspace_id,),
    ).fetchall()
    edge_rows = conn.execute(
        "SELECT source_id, target_id, kind, relationship, confidence, metadata FROM graph_edges WHERE workspace_id = %s ORDER BY id ASC",
        (workspace_id,),
    ).fetchall()
    state = conn.execute(
        "SELECT data FROM workspace_state WHERE workspace_id = %s",
        (workspace_id,),
    ).fetchone()

    thoughts_by_subnode = {}
    for t in thought_rows:
        item = dict(t.get("metadata") or {})
        item.update({
            "id": t["id"],
            "content": t["content"],
            "type": t["type"],
            "source": t["source"],
            "archived": bool(t["archived"]),
            "createdAt": _timestamp_to_iso(t["created_at"]),
        })
        thoughts_by_subnode.setdefault(t["subnode_id"], []).append(item)

    domains_by_id = {}
    nodes = []
    for d in domain_rows:
        item = dict(d.get("metadata") or {})
        item.update({
            "id": d["id"], "title": d["title"], "type": d["type"],
            "level": "domain", "x": d["x"], "y": d["y"],
            "thoughts": [],
        })
        domains_by_id[d["id"]] = item
        nodes.append(item)

    for s in sub_rows:
        item = dict(s.get("metadata") or {})
        item.update({
            "id": s["id"], "title": s["title"], "type": s["type"],
            "level": "subnode", "domain": domains_by_id.get(s["domain_id"], {}).get("title", ""),
            "x": s["x"], "y": s["y"],
            "thoughts": thoughts_by_subnode.get(s["id"], []),
        })
        nodes.append(item)

    edges = []
    for e in edge_rows:
        item = dict(e.get("metadata") or {})
        item.update({
            "source": e["source_id"], "target": e["target_id"],
            "kind": e["kind"], "relationship": e["relationship"],
            "confidence": e["confidence"],
        })
        edges.append(item)

    return {
        "root": {
            "title": workspace["startup_title"],
            "summary": workspace["summary"],
            "objective": workspace["objective"],
        },
        "nodes": nodes,
        "edges": edges,
        "insights": (state["data"] or {}).get("insights", []) if state else [],
        "questions": (state["data"] or {}).get("questions", []) if state else [],
    }


def save_graph(graph: dict) -> dict:
    workspace_id = current_workspace_id()
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        _ensure_workspace(conn, workspace_id)
        _sync_structured_workspace(conn, workspace_id, graph, now)
        # Keep the legacy JSONB document as a compatibility snapshot during the
        # transition. Normalized tables are the source of truth for new reads.
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
        structured = _load_structured_graph(conn, current_workspace_id())
        if structured is not None:
            return structured
        row = conn.execute(
            "SELECT data FROM founder_workspaces WHERE workspace_id = %s",
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


def create_chat_session(context_node_id: Optional[str] = None, title: str = "Founder Coach") -> dict:
    session_id = f"chat_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{_random_suffix()}"
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        _ensure_workspace(conn, current_workspace_id())
        conn.execute(
            """
            INSERT INTO chat_sessions
                (session_id, workspace_id, context_node_id, title, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (session_id, current_workspace_id(), context_node_id, title, now, now),
        )
    return {"sessionId": session_id, "contextNodeId": context_node_id, "title": title, "createdAt": now.isoformat(), "updatedAt": now.isoformat()}


def get_or_create_chat_session(session_id: Optional[str] = None, context_node_id: Optional[str] = None, title: str = "Founder Coach") -> dict:
    if session_id:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE session_id = %s AND workspace_id = %s",
                (session_id, current_workspace_id()),
            ).fetchone()
        if row:
            return {
                "sessionId": row["session_id"], "contextNodeId": row["context_node_id"],
                "title": row["title"], "createdAt": _timestamp_to_iso(row["created_at"]),
                "updatedAt": _timestamp_to_iso(row["updated_at"]),
            }
    return create_chat_session(context_node_id, title)


def save_chat_message(session_id: str, role: str, content: str, metadata: Optional[dict] = None) -> dict:
    if role not in {"user", "assistant", "system"}:
        raise ValueError("invalid chat role")
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO chat_messages
                (workspace_id, session_id, role, content, created_at, metadata)
            SELECT workspace_id, %s, %s, %s, %s, %s
            FROM chat_sessions
            WHERE session_id = %s AND workspace_id = %s
            RETURNING id, created_at
            """,
            (session_id, role, content, now, Jsonb(metadata or {}), session_id, current_workspace_id()),
        ).fetchone()
        if not row:
            raise ValueError("chat session not found")
        conn.execute(
            "UPDATE chat_sessions SET updated_at = %s WHERE session_id = %s AND workspace_id = %s",
            (now, session_id, current_workspace_id()),
        )
    return {"id": row["id"], "role": role, "content": content, "createdAt": _timestamp_to_iso(row["created_at"])}


def list_chat_messages(session_id: str, limit: int = 200) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, created_at, metadata
            FROM chat_messages
            WHERE session_id = %s AND workspace_id = %s
            ORDER BY created_at ASC, id ASC
            LIMIT %s
            """,
            (session_id, current_workspace_id(), limit),
        ).fetchall()
    return [
        {
            "id": r["id"], "role": r["role"], "content": r["content"],
            "createdAt": _timestamp_to_iso(r["created_at"]), "metadata": r["metadata"] or {},
        }
        for r in rows
    ]


def list_chat_sessions(context_node_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        if context_node_id is None:
            rows = conn.execute(
                """
                SELECT * FROM chat_sessions
                WHERE workspace_id = %s
                ORDER BY updated_at DESC LIMIT %s
                """,
                (current_workspace_id(), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM chat_sessions
                WHERE workspace_id = %s AND context_node_id = %s
                ORDER BY updated_at DESC LIMIT %s
                """,
                (current_workspace_id(), context_node_id, limit),
            ).fetchall()
    return [
        {
            "sessionId": r["session_id"], "contextNodeId": r["context_node_id"],
            "title": r["title"], "createdAt": _timestamp_to_iso(r["created_at"]),
            "updatedAt": _timestamp_to_iso(r["updated_at"]),
        }
        for r in rows
    ]


def healthcheck() -> None:
    """Raise if the PostgreSQL datastore is unreachable."""
    with get_conn() as conn:
        conn.execute("SELECT 1")


# ---------------------------------------------------------------------------
# Authentication / account ownership
# ---------------------------------------------------------------------------

def create_user(email: str, password_hash: str) -> dict:
    import secrets
    user_id = f"user_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{_random_suffix()}"
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (user_id, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
            (user_id, email.lower().strip(), password_hash, now),
        )
    return {"userId": user_id, "email": email.lower().strip(), "createdAt": now.isoformat()}

def get_user_by_email(email: str) -> Optional[dict]:
    with get_conn() as conn:
        return conn.execute("SELECT user_id, email, password_hash, created_at FROM users WHERE email = %s", (email.lower().strip(),)).fetchone()

def get_user(user_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT user_id, email, created_at FROM users WHERE user_id = %s", (user_id,)).fetchone()
    if not row:
        return None
    return {"userId": row["user_id"], "email": row["email"], "createdAt": _timestamp_to_iso(row["created_at"])}

def create_auth_session(user_id: str, ttl_days: int = 30) -> str:
    import secrets, hashlib
    from datetime import timedelta
    raw = secrets.token_urlsafe(32)
    token = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=ttl_days)
    with get_conn() as conn:
        conn.execute("INSERT INTO auth_sessions (session_id, user_id, created_at, expires_at) VALUES (%s, %s, %s, %s)", (token, user_id, now, expires))
    return raw

def get_user_id_from_auth_token(raw_token: Optional[str]) -> Optional[str]:
    if not raw_token:
        return None
    import hashlib
    token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with get_conn() as conn:
        row = conn.execute("SELECT user_id FROM auth_sessions WHERE session_id = %s AND expires_at > NOW()", (token,)).fetchone()
    return row["user_id"] if row else None

def revoke_auth_session(raw_token: Optional[str]) -> None:
    if not raw_token:
        return
    import hashlib
    token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    with get_conn() as conn:
        conn.execute("DELETE FROM auth_sessions WHERE session_id = %s", (token,))

def claim_workspace_for_user(workspace_id: str, user_id: str) -> bool:
    with get_conn() as conn:
        _ensure_workspace(conn, workspace_id)
        row = conn.execute("SELECT owner_user_id FROM workspaces WHERE workspace_id = %s", (workspace_id,)).fetchone()
        if not row:
            return False
        owner = row["owner_user_id"]
        if owner is None:
            conn.execute("UPDATE workspaces SET owner_user_id=%s, updated_at=NOW() WHERE workspace_id=%s", (user_id, workspace_id))
            return True
        return owner == user_id

def workspace_owned_by_user(workspace_id: str, user_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT owner_user_id FROM workspaces WHERE workspace_id=%s", (workspace_id,)).fetchone()
    return bool(row and row["owner_user_id"] == user_id)

def get_user_workspaces(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT workspace_id, startup_title, summary, objective, created_at, updated_at FROM workspaces WHERE owner_user_id=%s ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [{"workspaceId":r["workspace_id"],"title":r["startup_title"],"summary":r["summary"],"objective":r["objective"],"createdAt":_timestamp_to_iso(r["created_at"]),"updatedAt":_timestamp_to_iso(r["updated_at"])} for r in rows]
