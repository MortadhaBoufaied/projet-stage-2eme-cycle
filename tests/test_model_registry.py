"""Tests for ModelRegistry backed by SQLite metadata and on-disk joblib binaries.

Covers: save, load_latest, versions, activate, deactivate, list_companies,
JSON migration from pre-SQLite layout, and edge cases (empty data,
missing files, duplicate version stamps, sanitized company IDs).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from src.services.model_registry import ModelRegistry, safe_company_id, _ADMIN_COMPANY_ID


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_dir(tmp_path):
    """Create a fresh artifacts directory and redirect the shared DB there."""
    import src.services.db as db_mod
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    db_mod._DB_DIR = artifacts
    db_mod._DB_PATH = artifacts / "users.db"
    return artifacts


@pytest.fixture
def registry(db_dir):
    """Return a ModelRegistry pointing at the temporary artifacts dir."""
    return ModelRegistry(root=db_dir)


class DummyModel:
    """Minimal stand-in for a trained sklearn model."""
    def __init__(self, value=42):
        self.value = value


# ---------------------------------------------------------------------------
# safe_company_id
# ---------------------------------------------------------------------------

class TestSafeCompanyId:
    def test_alphanumeric_unchanged(self):
        assert safe_company_id("acme-corp_123") == "acme-corp_123"

    def test_special_chars_replaced(self):
        # @#$ is a single group of non-alnum chars, replaced with one underscore
        assert safe_company_id("acme/corp@#$") == "acme_corp_"

    def test_strips_whitespace(self):
        assert safe_company_id("  alice  ") == "alice"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            safe_company_id("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            safe_company_id("   ")

    def test_truncates_at_80(self):
        long_id = "a" * 100
        assert len(safe_company_id(long_id)) == 80


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

class TestSave:
    def test_save_creates_joblib_file(self, registry):
        path = registry.save("acme", "credit", DummyModel(), {"metrics": {"acc": 0.9}})
        assert path.exists()
        assert path.suffix == ".joblib"
        assert "acme" in str(path)

    def test_save_inserts_metadata_into_sqlite(self, registry):
        registry.save("acme", "credit", DummyModel(), {
            "metrics": {"acc": 0.9},
            "mapping": {"a": 1},
            "experiment": "train-all",
            "model_type": "RandomForest",
        })
        versions = registry.versions("acme", "credit")
        assert len(versions) == 1
        v = versions[0]
        assert v["metrics"] == {"acc": 0.9}
        assert v["mapping"] == {"a": 1}
        assert v["experiment"] == "train-all"
        assert v["model_type"] == "RandomForest"
        assert v["is_active"] is False  # new saves are inactive by default

    def test_save_with_none_mapping(self, registry):
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        v = registry.versions("acme", "credit")[0]
        assert v["mapping"] is None

    def test_save_with_data_summary(self, registry):
        summary = {"rows": 1000, "columns": 10}
        registry.save("acme", "credit", DummyModel(), {"metrics": {}, "data_summary": summary})
        v = registry.versions("acme", "credit")[0]
        assert v["data_summary"] == summary

    def test_save_sanitizes_company_id(self, registry):
        path = registry.save("acme/corp", "credit", DummyModel(), {"metrics": {}})
        assert "acme_corp" in str(path)

    def test_save_multiple_versions(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save("acme", "credit", DummyModel(2), {"metrics": {"v": 2}})
        versions = registry.versions("acme", "credit")
        assert len(versions) == 2


# ---------------------------------------------------------------------------
# load_latest
# ---------------------------------------------------------------------------

class TestLoadLatest:
    def test_load_latest_returns_model_and_meta(self, registry):
        registry.save("acme", "credit", DummyModel(99), {"metrics": {"acc": 0.85}})
        model, meta = registry.load_latest("acme", "credit")
        assert isinstance(model, DummyModel)
        assert model.value == 99
        assert meta["metrics"] == {"acc": 0.85}

    def test_load_latest_returns_newest_when_no_active(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save("acme", "credit", DummyModel(2), {"metrics": {"v": 2}})
        model, meta = registry.load_latest("acme", "credit")
        assert model.value == 2

    def test_load_latest_returns_active_over_newest(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save("acme", "credit", DummyModel(2), {"metrics": {"v": 2}})
        # Activate the older version
        versions = registry.versions("acme", "credit")
        older = [v for v in versions if v["metrics"]["v"] == 1][0]
        registry.activate("acme", "credit", older["version"])
        model, meta = registry.load_latest("acme", "credit")
        assert model.value == 1

    def test_load_latest_raises_when_no_versions(self, registry):
        with pytest.raises(FileNotFoundError, match="No saved"):
            registry.load_latest("nonexistent", "credit")

    def test_load_latest_raises_when_joblib_missing(self, registry, db_dir):
        """Simulate a deleted joblib file while metadata still exists."""
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        v = registry.versions("acme", "credit")[0]
        joblib_path = db_dir / "acme" / "credit" / v["model_file"]
        joblib_path.unlink()
        with pytest.raises(FileNotFoundError, match="not found on disk"):
            registry.load_latest("acme", "credit")


# ---------------------------------------------------------------------------
# versions
# ---------------------------------------------------------------------------

class TestVersions:
    def test_versions_returns_empty_for_unknown(self, registry):
        assert registry.versions("nobody", "credit") == []

    def test_versions_ordered_newest_first(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {}})
        registry.save("acme", "credit", DummyModel(2), {"metrics": {}})
        versions = registry.versions("acme", "credit")
        # saved_at_utc is a timestamp string; last saved should sort first
        assert versions[0]["saved_at_utc"] >= versions[1]["saved_at_utc"]

    def test_versions_independent_per_task(self, registry):
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        registry.save("acme", "forecast", DummyModel(), {"metrics": {}})
        assert len(registry.versions("acme", "credit")) == 1
        assert len(registry.versions("acme", "forecast")) == 1

    def test_versions_independent_per_company(self, registry):
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        registry.save("bobco", "credit", DummyModel(), {"metrics": {}})
        assert len(registry.versions("acme", "credit")) == 1
        assert len(registry.versions("bobco", "credit")) == 1

    def test_versions_falls_back_to_admin_when_company_empty(self, registry):
        """Company users see admin-trained models when they have none."""
        registry.save(_ADMIN_COMPANY_ID, "credit", DummyModel(1), {"metrics": {"acc": 0.9}})
        # Company user 'alice' has no models -- should see admin versions
        versions = registry.versions("alice", "credit")
        assert len(versions) == 1
        assert versions[0]["metrics"] == {"acc": 0.9}

    def test_versions_uses_own_when_available(self, registry):
        """Company users see their own models, not admin models."""
        registry.save(_ADMIN_COMPANY_ID, "credit", DummyModel(1), {"metrics": {"from": "admin"}})
        registry.save("alice", "credit", DummyModel(2), {"metrics": {"from": "alice"}})
        versions = registry.versions("alice", "credit")
        assert len(versions) == 1
        assert versions[0]["metrics"]["from"] == "alice"


# ---------------------------------------------------------------------------
# Admin fallback (load_latest_with_admin_fallback)
# ---------------------------------------------------------------------------

class TestAdminFallback:
    def test_loads_own_model_when_available(self, registry):
        """Company user's own active model takes priority."""
        registry.save("alice", "credit", DummyModel(42), {"metrics": {"acc": 0.85}})
        registry.activate("alice", "credit", registry.versions("alice", "credit")[0]["version"])
        model, meta = registry.load_latest_with_admin_fallback("alice", "credit")
        assert model.value == 42

    def test_falls_back_to_admin_when_no_own_model(self, registry):
        """Company user with no models gets the admin's active model."""
        registry.save(_ADMIN_COMPANY_ID, "credit", DummyModel(99), {"metrics": {"acc": 0.9}})
        registry.activate(
            _ADMIN_COMPANY_ID, "credit",
            registry.versions(_ADMIN_COMPANY_ID, "credit")[0]["version"],
        )
        model, meta = registry.load_latest_with_admin_fallback("alice", "credit")
        assert model.value == 99
        assert meta["metrics"] == {"acc": 0.9}

    def test_raises_when_neither_company_nor_admin_have_models(self, registry):
        """Both company and admin namespaces empty -- raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="No saved"):
            registry.load_latest_with_admin_fallback("nobody", "credit")

    def test_admin_company_does_not_double_fallback(self, registry):
        """When the admin itself calls, the fallback should not recurse."""
        with pytest.raises(FileNotFoundError, match="No saved"):
            registry.load_latest_with_admin_fallback(_ADMIN_COMPANY_ID, "credit")

    def test_fallback_loads_admin_newest_when_no_active(self, registry):
        """Fallback returns newest admin version when none is active."""
        registry.save(_ADMIN_COMPANY_ID, "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save(_ADMIN_COMPANY_ID, "credit", DummyModel(2), {"metrics": {"v": 2}})
        model, meta = registry.load_latest_with_admin_fallback("alice", "credit")
        assert model.value == 2


# ---------------------------------------------------------------------------
# activate / deactivate
# ---------------------------------------------------------------------------

class TestActivate:
    def test_activate_sets_is_active(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save("acme", "credit", DummyModel(2), {"metrics": {"v": 2}})
        versions = registry.versions("acme", "credit")
        target = [v for v in versions if v["metrics"]["v"] == 1][0]
        registry.activate("acme", "credit", target["version"])
        refreshed = registry.versions("acme", "credit")
        active = [v for v in refreshed if v["is_active"]]
        assert len(active) == 1
        assert active[0]["version"] == target["version"]

    def test_activate_deactivates_previous(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save("acme", "credit", DummyModel(2), {"metrics": {"v": 2}})
        v1 = registry.versions("acme", "credit")
        registry.activate("acme", "credit", v1[0]["version"])
        registry.activate("acme", "credit", v1[1]["version"])
        refreshed = registry.versions("acme", "credit")
        active = [v for v in refreshed if v["is_active"]]
        assert len(active) == 1
        assert active[0]["version"] == v1[1]["version"]

    def test_activate_raises_for_missing_version(self, registry):
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        with pytest.raises(FileNotFoundError, match="not found"):
            registry.activate("acme", "credit", "nonexistent_version")

    def test_activate_only_affects_same_task(self, registry):
        registry.save("acme", "credit", DummyModel(1), {"metrics": {"v": 1}})
        registry.save("acme", "forecast", DummyModel(2), {"metrics": {"v": 2}})
        v_credit = registry.versions("acme", "credit")[0]
        v_forecast = registry.versions("acme", "forecast")[0]
        registry.activate("acme", "credit", v_credit["version"])
        registry.activate("acme", "forecast", v_forecast["version"])
        assert registry.versions("acme", "credit")[0]["is_active"] is True
        assert registry.versions("acme", "forecast")[0]["is_active"] is True


# ---------------------------------------------------------------------------
# list_companies
# ---------------------------------------------------------------------------

class TestListCompanies:
    def test_list_companies_empty(self, registry):
        assert registry.list_companies() == []

    def test_list_companies_returns_sorted(self, registry):
        registry.save("bobco", "credit", DummyModel(), {"metrics": {}})
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        assert registry.list_companies() == ["acme", "bobco"]


# ---------------------------------------------------------------------------
# migrate_from_json
# ---------------------------------------------------------------------------

class TestMigrateFromJson:
    def test_migrates_json_metadata_files(self, registry, db_dir):
        """Simulate the pre-SQLite layout with metadata_*.json files."""
        task_dir = db_dir / "acme" / "credit"
        task_dir.mkdir(parents=True)

        # Write a legacy metadata file
        meta = {
            "version": "20260101T120000",
            "model_file": "model_20260101T120000.joblib",
            "metrics": {"acc": 0.8},
            "mapping": {"x": "y"},
            "experiment": "manual",
            "model_type": "XGB",
            "saved_at_utc": "2026-01-01T12:00:00Z",
        }
        (task_dir / "metadata_20260101T120000.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )

        count = registry.migrate_from_json("acme", "credit")
        assert count == 1

        versions = registry.versions("acme", "credit")
        assert len(versions) == 1
        assert versions[0]["metrics"] == {"acc": 0.8}
        assert versions[0]["mapping"] == {"x": "y"}

    def test_migration_is_idempotent(self, registry, db_dir):
        task_dir = db_dir / "acme" / "credit"
        task_dir.mkdir(parents=True)
        meta = {
            "version": "20260101T120000",
            "model_file": "model_20260101T120000.joblib",
            "metrics": {},
            "saved_at_utc": "2026-01-01T12:00:00Z",
        }
        (task_dir / "metadata_20260101T120000.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        registry.migrate_from_json("acme", "credit")
        count = registry.migrate_from_json("acme", "credit")
        assert count == 0  # second run imports nothing
        assert len(registry.versions("acme", "credit")) == 1

    def test_migration_skips_corrupt_json(self, registry, db_dir):
        task_dir = db_dir / "acme" / "credit"
        task_dir.mkdir(parents=True)
        (task_dir / "metadata_corrupt.json").write_text("not json!!!", encoding="utf-8")
        count = registry.migrate_from_json("acme", "credit")
        assert count == 0

    def test_migration_handles_empty_directory(self, registry):
        count = registry.migrate_from_json("acme", "credit")
        assert count == 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_save_and_load_with_empty_metrics(self, registry):
        registry.save("acme", "credit", DummyModel(), {"metrics": {}})
        model, meta = registry.load_latest("acme", "credit")
        assert meta["metrics"] == {}

    def test_company_dir_created_on_save(self, registry, db_dir):
        registry.save("newcompany", "credit", DummyModel(), {"metrics": {}})
        assert (db_dir / "newcompany").is_dir()
        assert (db_dir / "newcompany" / "credit").is_dir()

    def test_company_dir_not_created_without_flag(self, registry, db_dir):
        d = registry.company_dir("other", create=False)
        assert not d.exists()

    def test_unicode_company_id(self, registry):
        registry.save("entreprise_francaise", "credit", DummyModel(), {"metrics": {}})
        versions = registry.versions("entreprise_francaise", "credit")
        assert len(versions) == 1
