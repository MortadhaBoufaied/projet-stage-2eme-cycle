from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from src.config import ADMIN_PASSWORD, ADMIN_USERNAME, SESSION_MINUTES

# -- Session keys -----------------------------------------------------------
AUTH_KEY = "finance_authenticated"
USER_KEY = "finance_user"
EXPIRY_KEY = "finance_session_expiry"

# -- SQLite user store ------------------------------------------------------
_DB_DIR = Path(__file__).resolve().parents[2] / "artifacts"
_DB_PATH = _DB_DIR / "users.db"


def _get_db() -> sqlite3.Connection:
    """Return a connection to the users database. Creates the table on first use."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  username TEXT UNIQUE NOT NULL,"
        "  password_hash TEXT NOT NULL,"
        "  salt TEXT NOT NULL,"
        "  created_at TEXT NOT NULL"
        ")"
    )
    conn.commit()
    return conn


def _hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Hash a password with PBKDF2-SHA256. Returns (digest, salt)."""
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return digest, salt


def credentials_configured() -> bool:
    """Return True if the admin .env credentials are set."""
    return bool(ADMIN_USERNAME and ADMIN_PASSWORD)


def _verify_admin(username: str, password: str) -> bool:
    """Check against the .env admin credentials."""
    if not credentials_configured():
        return False
    return (
        hmac.compare_digest(username.strip(), ADMIN_USERNAME)
        and hmac.compare_digest(password, ADMIN_PASSWORD)
    )


def _verify_registered_user(username: str, password: str) -> bool:
    """Check against the registered user store in SQLite."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT password_hash, salt FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
        if row is None:
            return False
        stored_hash = bytes.fromhex(row[0])
        stored_salt = bytes.fromhex(row[1])
        candidate_hash, _ = _hash_password(password, stored_salt)
        return hmac.compare_digest(candidate_hash, stored_hash)
    finally:
        conn.close()


def sign_in(username: str, password: str) -> bool:
    """Authenticate against admin credentials or registered users.
    Sets session state on success. Returns True if valid."""
    valid = _verify_admin(username, password) or _verify_registered_user(username, password)
    if valid:
        st.session_state[AUTH_KEY] = True
        st.session_state[USER_KEY] = username.strip()
        st.session_state[EXPIRY_KEY] = datetime.now(timezone.utc) + timedelta(minutes=SESSION_MINUTES)
    return valid


def sign_up(username: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if len(password) > 128:
        return False, "Password must be at most 128 characters."

    # Reject registration if the username matches the admin account
    if credentials_configured() and username.lower() == ADMIN_USERNAME.lower():
        return False, "This username is reserved. Use the admin login."

    conn = _get_db()
    try:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username.lower(),)
        ).fetchone()
        if exists is not None:
            return False, "An account with this username already exists."

        digest, salt = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
            (username.lower(), digest.hex(), salt.hex(), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return True, "Account created. You can now sign in."
    finally:
        conn.close()


def is_authenticated() -> bool:
    """Return True if the current session is valid and not expired."""
    expiry = st.session_state.get(EXPIRY_KEY)
    if (
        not st.session_state.get(AUTH_KEY)
        or not expiry
        or datetime.now(timezone.utc) >= expiry
    ):
        sign_out()
        return False
    return True


def current_user() -> str:
    """Return the username of the currently authenticated user."""
    return str(st.session_state.get(USER_KEY, ""))


def sign_out() -> None:
    """Clear all authentication session state."""
    for key in (AUTH_KEY, USER_KEY, EXPIRY_KEY):
        st.session_state.pop(key, None)
