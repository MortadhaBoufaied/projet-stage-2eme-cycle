"""Audit log service for the Finance Decision Studio.

Records security-relevant and operational events to the audit_log table.
All calls are fire-and-forget: exceptions are swallowed so audit failures
never break the application UI.

Design decisions:
- Append-only: no UPDATE or DELETE operations exist on audit_log.
- Compact payloads: detail stores a short JSON summary, not full metrics.
- Bootstrap/profile-init saves in app.py are NOT audited (they are no-ops).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from src.services.db import _get_db


class AuditEvent:
    """Constants for auditable event types."""

    AUTH_SIGN_IN = "auth.sign_in"
    AUTH_SIGN_IN_FAIL = "auth.sign_in_fail"
    AUTH_SIGN_UP = "auth.sign_up"
    AUTH_SIGN_OUT = "auth.sign_out"
    MODEL_TRAIN = "model.train"
    MODEL_ACTIVATE = "model.activate"
    POLICY_UPDATE = "policy.update"


def log_event(
    event_type: str,
    username: str = "",
    role: str = "",
    company_id: str = "",
    detail: dict | None = None,
) -> None:
    """Write a single audit log entry. Never raises."""
    try:
        conn = _get_db()
        try:
            conn.execute(
                "INSERT INTO audit_log (timestamp, event_type, username, role, company_id, detail)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    event_type,
                    username,
                    role,
                    company_id,
                    json.dumps(detail, ensure_ascii=False) if detail else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def query_events(
    event_type: str | None = None,
    username: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return recent audit entries, newest first. Filters are optional."""
    conn = _get_db()
    try:
        sql = "SELECT id, timestamp, event_type, username, role, company_id, detail FROM audit_log"
        params: list = []
        conditions: list = []
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if username:
            conditions.append("username = ?")
            params.append(username)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        entry = {
            "id": row[0],
            "timestamp": row[1],
            "event_type": row[2],
            "username": row[3],
            "role": row[4],
            "company_id": row[5],
        }
        if row[6]:
            try:
                entry["detail"] = json.loads(row[6])
            except (json.JSONDecodeError, TypeError):
                entry["detail"] = row[6]
        results.append(entry)
    return results
