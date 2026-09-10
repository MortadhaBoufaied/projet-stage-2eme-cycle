"""End-to-end tests for the authentication system.

Covers: sign up, sign in, sign out, duplicate rejection, admin reservation,
password hashing, SQLite persistence, and session expiry.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path: Path):
    """Return an auth module bound to a temporary SQLite database.

    Redirects the module-level _DB_DIR and _DB_PATH in ``db.py`` so every
    call to ``_get_db()`` uses an isolated database under *tmp_path*.
    Because *tmp_path* is per-test and cleaned up by pytest, there is no
    need to restore the original values.
    """
    db_dir = tmp_path / "artifacts"
    db_dir.mkdir()

    import src.services.db as db_mod
    db_mod._DB_DIR = db_dir
    db_mod._DB_PATH = db_dir / "users.db"

    import src.services.auth as auth_mod
    return auth_mod, db_dir


# ---------------------------------------------------------------------------
# Sign-up tests
# ---------------------------------------------------------------------------

class TestSignUp:
    def test_successful_registration(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        ok, msg = auth.sign_up("alice", "secure123")
        assert ok is True
        assert "created" in msg.lower()

    def test_duplicate_username_rejected(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        auth.sign_up("alice", "secure123")
        ok, msg = auth.sign_up("alice", "another123")
        assert ok is False
        assert "already exists" in msg.lower()

    def test_case_insensitive_duplicates(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        auth.sign_up("Alice", "secure123")
        ok, _ = auth.sign_up("alice", "secure123")
        assert ok is False

    def test_empty_username_rejected(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        ok, msg = auth.sign_up("", "secure123")
        assert ok is False
        assert "required" in msg.lower()

    def test_empty_password_rejected(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        ok, msg = auth.sign_up("alice", "")
        assert ok is False
        assert "required" in msg.lower()

    def test_short_password_rejected(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        ok, msg = auth.sign_up("alice", "ab")
        assert ok is False
        assert "6 characters" in msg

    def test_long_password_rejected(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        ok, msg = auth.sign_up("alice", "a" * 129)
        assert ok is False
        assert "128 characters" in msg

    def test_admin_username_reserved(self, tmp_path):
        auth, _ = _fresh_db(tmp_path)
        with patch.dict(os.environ, {"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "pass"}):
            auth.ADMIN_USERNAME = "admin"
            auth.ADMIN_PASSWORD = "pass"
            ok, msg = auth.sign_up("admin", "secure123")
            assert ok is False
            assert "reserved" in msg.lower()

    def test_password_is_hashed_not_stored_plaintext(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("alice", "mysecretpassword")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        row = conn.execute("SELECT password_hash, salt FROM users WHERE username='alice'").fetchone()
        conn.close()
        assert row is not None
        assert row[0] != "mysecretpassword"
        assert len(row[0]) == 64  # SHA256 hex digest
        assert len(bytes.fromhex(row[1])) == 16  # 16-byte salt

    def test_user_persisted_in_sqlite(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("bob", "secure123")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        assert count == 1


# ---------------------------------------------------------------------------
# Sign-in tests
# ---------------------------------------------------------------------------

class TestSignIn:
    def test_valid_registered_user(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        monkeypatch.setattr("src.services.auth.st.session_state", {})
        auth.sign_up("alice", "secure123")
        result = auth.sign_in("alice", "secure123")
        assert result is True

    def test_wrong_password_rejected(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        monkeypatch.setattr("src.services.auth.st.session_state", {})
        auth.sign_up("alice", "secure123")
        result = auth.sign_in("alice", "wrongpassword")
        assert result is False

    def test_nonexistent_user_rejected(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        monkeypatch.setattr("src.services.auth.st.session_state", {})
        result = auth.sign_in("nobody", "secure123")
        assert result is False

    def test_admin_env_credentials_work(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        monkeypatch.setattr("src.services.auth.st.session_state", {})
        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.setenv("ADMIN_PASSWORD", "adminpass")
        auth.ADMIN_USERNAME = "admin"
        auth.ADMIN_PASSWORD = "adminpass"
        result = auth.sign_in("admin", "adminpass")
        assert result is True

    def test_admin_wrong_password_rejected(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        monkeypatch.setattr("src.services.auth.st.session_state", {})
        monkeypatch.setattr("src.services.auth.ADMIN_USERNAME", "admin")
        monkeypatch.setattr("src.services.auth.ADMIN_PASSWORD", "adminpass")
        result = auth.sign_in("admin", "wrong")
        assert result is False

    def test_session_keys_set_on_success(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        auth.sign_up("alice", "secure123")
        auth.sign_in("alice", "secure123")
        assert fake_state.get(auth.AUTH_KEY) is True
        assert fake_state.get(auth.USER_KEY) == "alice"
        assert auth.EXPIRY_KEY in fake_state
        assert fake_state.get(auth.ROLE_KEY) == "company"
        assert fake_state.get(auth.COMPANY_KEY) == "alice"

    def test_admin_session_keys_set_on_success(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        monkeypatch.setattr("src.services.auth.ADMIN_USERNAME", "admin")
        monkeypatch.setattr("src.services.auth.ADMIN_PASSWORD", "adminpass")
        auth.sign_in("admin", "adminpass")
        assert fake_state.get(auth.ROLE_KEY) == "admin"
        assert fake_state.get(auth.COMPANY_KEY) == "admin_company"

    def test_session_keys_not_set_on_failure(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        auth.sign_in("alice", "wrongpassword")
        assert auth.AUTH_KEY not in fake_state


# ---------------------------------------------------------------------------
# Session management tests
# ---------------------------------------------------------------------------

class TestSessionManagement:
    def test_is_authenticated_true_when_valid(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {
            auth.AUTH_KEY: True,
            auth.USER_KEY: "alice",
            auth.EXPIRY_KEY: datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.is_authenticated() is True

    def test_is_authenticated_false_when_expired(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {
            auth.AUTH_KEY: True,
            auth.USER_KEY: "alice",
            auth.EXPIRY_KEY: datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.is_authenticated() is False

    def test_is_authenticated_false_when_no_auth_key(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.is_authenticated() is False

    def test_sign_out_clears_session(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {
            auth.AUTH_KEY: True,
            auth.USER_KEY: "alice",
            auth.EXPIRY_KEY: datetime.now(timezone.utc) + timedelta(minutes=10),
            auth.ROLE_KEY: "company",
            auth.COMPANY_KEY: "alice",
        }
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        auth.sign_out()
        assert auth.AUTH_KEY not in fake_state
        assert auth.USER_KEY not in fake_state
        assert auth.EXPIRY_KEY not in fake_state
        assert auth.ROLE_KEY not in fake_state
        assert auth.COMPANY_KEY not in fake_state

    def test_current_user_returns_username(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {auth.USER_KEY: "alice"}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_user() == "alice"

    def test_current_user_returns_empty_when_no_session(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_user() == ""

    def test_credentials_configured_true_when_env_set(self, monkeypatch):
        import src.services.auth as auth_mod
        monkeypatch.setattr("src.services.auth.ADMIN_USERNAME", "admin")
        monkeypatch.setattr("src.services.auth.ADMIN_PASSWORD", "pass")
        assert auth_mod.credentials_configured() is True

    def test_credentials_configured_false_when_env_missing(self, monkeypatch):
        import src.services.auth as auth_mod
        monkeypatch.setattr("src.services.auth.ADMIN_USERNAME", "")
        monkeypatch.setattr("src.services.auth.ADMIN_PASSWORD", "")
        assert auth_mod.credentials_configured() is False

    def test_current_role_returns_company_for_registered_user(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {auth.ROLE_KEY: "company"}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_role() == "company"

    def test_current_role_returns_admin_for_admin_user(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {auth.ROLE_KEY: "admin"}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_role() == "admin"

    def test_current_role_defaults_to_company(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_role() == "company"

    def test_current_company_returns_username_for_registered_user(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {auth.COMPANY_KEY: "alice"}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_company() == "alice"

    def test_current_company_returns_admin_company_for_admin(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {auth.COMPANY_KEY: "admin_company"}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_company() == "admin_company"

    def test_current_company_defaults_to_admin_company(self, tmp_path, monkeypatch):
        auth, _ = _fresh_db(tmp_path)
        fake_state = {}
        monkeypatch.setattr("src.services.auth.st.session_state", fake_state)
        assert auth.current_company() == "admin_company"

    def test_users_table_has_role_column(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("alice", "secure123")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        columns = conn.execute("PRAGMA table_info(users)").fetchall()
        conn.close()
        col_names = [c[1] for c in columns]
        assert "role" in col_names

    def test_registered_user_role_defaults_to_company(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("alice", "secure123")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        row = conn.execute("SELECT role FROM users WHERE username='alice'").fetchone()
        conn.close()
        assert row[0] == "company"


# ---------------------------------------------------------------------------
# SQLite integrity tests
# ---------------------------------------------------------------------------

class TestSQLiteIntegrity:
    def test_wal_mode_enabled(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("alice", "secure123")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_table_schema_correct(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("alice", "secure123")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        columns = conn.execute("PRAGMA table_info(users)").fetchall()
        conn.close()
        col_names = [c[1] for c in columns]
        assert "id" in col_names
        assert "username" in col_names
        assert "password_hash" in col_names
        assert "salt" in col_names
        assert "created_at" in col_names

    def test_username_unique_constraint(self, tmp_path):
        auth, db_dir = _fresh_db(tmp_path)
        auth.sign_up("alice", "secure123")
        auth.sign_up("alice", "another123")
        conn = sqlite3.connect(str(db_dir / "users.db"))
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        assert count == 1  # second insert rejected by UNIQUE constraint
