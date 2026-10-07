"""One-time migration from the old SQLite store to PostgreSQL.

Usage:
    DATABASE_URL='postgresql://...' python scripts/migrate_sqlite_to_postgres.py

The migration preserves every workspace_id from the SQLite graph store.
Legacy decisions/config, which predated workspace scoping, are placed in the
"local" workspace so they remain accessible without inventing ownership.
"""

import argparse
import sqlite3
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

import sys

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import db


def migrate(sqlite_path: Path, allow_existing: bool = False) -> dict:
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    db.init_db()

    with psycopg.connect(db.DATABASE_URL) as target:
        existing = target.execute("SELECT COUNT(*) AS n FROM founder_workspaces").fetchone()[0]
        if existing and not allow_existing:
            raise RuntimeError(
                "PostgreSQL already contains workspaces. "
                "Use --allow-existing only after reviewing the target database."
            )

        with sqlite3.connect(str(sqlite_path)) as source:
            source.row_factory = sqlite3.Row

            workspace_rows = source.execute(
                "SELECT workspace_id, data, updated_at FROM founder_workspaces"
            ).fetchall()
            for row in workspace_rows:
                target.execute(
                    """
                    INSERT INTO founder_workspaces (workspace_id, data, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (workspace_id) DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (row["workspace_id"], Jsonb(_json_load(row["data"])), row["updated_at"]),
                )

            if _table_exists(source, "decisions"):
                target.execute(
                    """
                    INSERT INTO founder_workspaces (workspace_id, data, updated_at)
                    VALUES ('local', %s, NOW())
                    ON CONFLICT (workspace_id) DO NOTHING
                    """,
                    (Jsonb(db._empty_graph()),),
                )
                decisions = source.execute("SELECT * FROM decisions").fetchall()
                for row in decisions:
                    target.execute(
                        """
                        INSERT INTO decisions (
                            workspace_id, id, question, mode, result, brief,
                            created_at, executed, regret, dialogue_history
                        )
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
                            "local",
                            row["id"],
                            row["question"],
                            row["mode"],
                            Jsonb(_json_load(row["result"])),
                            Jsonb(_json_load(row["brief"])) if row["brief"] else None,
                            row["created_at"],
                            bool(row["executed"]),
                            bool(row["regret"]),
                            Jsonb(_json_load(row["dialogue_history"])) if row["dialogue_history"] else None,
                        ),
                    )

            if _table_exists(source, "config"):
                target.execute(
                    """
                    INSERT INTO founder_workspaces (workspace_id, data, updated_at)
                    VALUES ('local', %s, NOW())
                    ON CONFLICT (workspace_id) DO NOTHING
                    """,
                    (Jsonb(db._empty_graph()),),
                )
                configs = source.execute("SELECT key, value FROM config").fetchall()
                for row in configs:
                    target.execute(
                        """
                        INSERT INTO config (workspace_id, key, value)
                        VALUES ('local', %s, %s)
                        ON CONFLICT (workspace_id, key) DO UPDATE SET
                            value = EXCLUDED.value
                        """,
                        (row["key"], Jsonb(_json_load(row["value"]))),
                    )

    print(f"Migrated {len(workspace_rows)} workspace graph(s) from {sqlite_path}")


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _json_load(value):
    import json

    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate FounderOS SQLite data to PostgreSQL.")
    parser.add_argument(
        "--sqlite",
        default=str(Path(__file__).resolve().parents[1] / "backend" / "choice.db"),
        help="Path to the legacy choice.db file.",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Allow migration into a PostgreSQL database that already has workspaces.",
    )
    args = parser.parse_args()
    migrate(Path(args.sqlite), allow_existing=args.allow_existing)
