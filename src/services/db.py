"""Shared SQLite connection and schema for the Finance Decision Studio.

All persistent data (user credentials, model metadata) lives in one database
under ARTIFACTS_DIR/users.db.  Model binary files (joblib) remain on disk
and are referenced by path from the model_versions table.

Design decisions:
- WAL journal mode for concurrent-safe reads during Streamlit reruns.
- Single connection per process (thread-safe for Streamlit's single-threaded
  execution model; safe enough for test isolation via monkeypatch).
- Schema migration is additive -- new tables are created IF NOT EXISTS so
  existing databases upgrade transparently.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import ARTIFACTS_DIR

_DB_DIR = ARTIFACTS_DIR
_DB_PATH = _DB_DIR / "users.db"

_SCHEMA_VERSION = 2


def _get_db() -> sqlite3.Connection:
    """Return a connection to the shared application database.

    Creates the artifacts directory and all tables on first use.
    Sets WAL journal mode for concurrent-safe reads.
    """
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables that do not yet exist. Safe to call repeatedly."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  username TEXT UNIQUE NOT NULL,"
        "  password_hash TEXT NOT NULL,"
        "  salt TEXT NOT NULL,"
        "  created_at TEXT NOT NULL"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS model_versions ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  company_id TEXT NOT NULL,"
        "  task TEXT NOT NULL,"
        "  version TEXT NOT NULL,"
        "  model_file TEXT NOT NULL,"
        "  metrics TEXT NOT NULL,"
        "  mapping TEXT,"
        "  data_summary TEXT,"
        "  experiment TEXT,"
        "  model_type TEXT,"
        "  is_active INTEGER NOT NULL DEFAULT 0,"
        "  saved_at_utc TEXT NOT NULL,"
        "  UNIQUE(company_id, task, version)"
        ")"
    )
    # -- Schema migrations (additive, idempotent) --------------------------
    # v2: add role column to users table
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'company'")

    conn.commit()
