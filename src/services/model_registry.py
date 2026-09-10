"""Model registry backed by SQLite metadata and on-disk joblib binaries.

Model binary files (sklearn pipelines, etc.) are serialized with joblib
to ``{artifacts}/{company_id}/{task}/model_{version}.joblib``.  All metadata
(metrics, hyperparameters, mapping, activation status) lives in the
``model_versions`` table of the shared SQLite database managed by
``src.services.db``.

Design decisions:
- Joblib files stay on disk because they are opaque Python object graphs
  that cannot be meaningfully queried.  SQLite stores only the metadata
  needed for listing, comparing, and activating versions.
- An ``is_active`` boolean column replaces the old ``latest.json`` symlink
  pattern.  Only one version per (company, task) pair can be active.
- A ``versions()`` query replaces the old ``glob('metadata_*.json')`` scan.
- ``safe_company_id()`` is preserved for backward compatibility with
  existing directory layouts.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import joblib

from src.config import ARTIFACTS_DIR
from src.services.db import _get_db


# When a company user has no models, fall back to models stored under this
# namespace.  Admin-trained models are shared across all company users.
_ADMIN_COMPANY_ID = "admin_company"


def safe_company_id(value: str) -> str:
    """Sanitize a company identifier for use as a directory name."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    if not cleaned:
        raise ValueError("Company ID cannot be empty.")
    return cleaned[:80]


class ModelRegistry:
    """File-and-SQLite model registry.

    Binaries are written to ``{root}/{company_id}/{task}/``.
    Metadata is queried from the ``model_versions`` table.
    """

    def __init__(self, root: Path = ARTIFACTS_DIR) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- Directory helpers ---------------------------------------------------

    def company_dir(self, company_id: str, create: bool = False) -> Path:
        """Return (and optionally create) the directory for a company."""
        p = self.root / safe_company_id(company_id)
        if create:
            p.mkdir(parents=True, exist_ok=True)
        return p

    def _task_dir(self, company_id: str, task: str, create: bool = False) -> Path:
        """Return the directory that holds binaries for a specific task."""
        d = self.company_dir(company_id, create) / task
        if create:
            d.mkdir(parents=True, exist_ok=True)
        return d

    # -- Core operations -----------------------------------------------------

    def save(
        self,
        company_id: str,
        task: str,
        model,
        metadata: dict,
    ) -> Path:
        """Persist a trained model and its metadata.

        Returns the path to the saved joblib file.
        """
        task_dir = self._task_dir(company_id, task, create=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

        # Write binary to disk
        model_path = task_dir / f"model_{stamp}.joblib"
        joblib.dump(model, model_path)

        # Insert metadata into SQLite
        conn = _get_db()
        try:
            conn.execute(
                "INSERT INTO model_versions"
                " (company_id, task, version, model_file, metrics, mapping,"
                "  data_summary, experiment, model_type, is_active, saved_at_utc)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                (
                    safe_company_id(company_id),
                    task,
                    stamp,
                    model_path.name,
                    json.dumps(metadata.get("metrics", {}), ensure_ascii=False),
                    json.dumps(metadata.get("mapping"), ensure_ascii=False)
                    if metadata.get("mapping") is not None
                    else None,
                    json.dumps(metadata.get("data_summary"), ensure_ascii=False)
                    if metadata.get("data_summary") is not None
                    else None,
                    metadata.get("experiment"),
                    metadata.get("model_type"),
                    stamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return model_path

    def load_latest(self, company_id: str, task: str):
        """Load the active model and its metadata.

        If no version is active, loads the most recently saved version.
        Returns (model_object, metadata_dict).
        Raises FileNotFoundError if no versions exist.
        """
        task_dir = self._task_dir(company_id, task)

        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT task, version, model_file, metrics, mapping, data_summary,"
                " experiment, model_type, is_active, saved_at_utc"
                " FROM model_versions"
                " WHERE company_id = ? AND task = ?"
                " ORDER BY is_active DESC, saved_at_utc DESC"
                " LIMIT 1",
                (safe_company_id(company_id), task),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            raise FileNotFoundError(f"No saved {task} model for {company_id}.")

        meta = self._row_to_dict(row)
        model_path = task_dir / meta["model_file"]
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file {meta['model_file']} not found on disk."
            )
        return joblib.load(model_path), meta

    def load_latest_with_admin_fallback(
        self, company_id: str, task: str
    ):
        """Load the active model for *company_id*, falling back to the admin namespace.

        Company users consume admin-trained models.  If the requesting company
        has no saved versions for *task*, this method retries the query under
        ``_ADMIN_COMPANY_ID`` before raising FileNotFoundError.

        Returns (model_object, metadata_dict).
        """
        try:
            return self.load_latest(company_id, task)
        except FileNotFoundError:
            if company_id == _ADMIN_COMPANY_ID:
                raise
            return self.load_latest(_ADMIN_COMPANY_ID, task)

    def versions(self, company_id: str, task: str) -> list[dict]:
        """Return all saved versions for a company/task, newest first.

        If the requesting company has no versions, falls back to the admin
        namespace so company users can see admin-trained model history.
        """
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT task, version, model_file, metrics, mapping, data_summary,"
                " experiment, model_type, is_active, saved_at_utc"
                " FROM model_versions"
                " WHERE company_id = ? AND task = ?"
                " ORDER BY saved_at_utc DESC",
                (safe_company_id(company_id), task),
            ).fetchall()

            # Fallback: if the company has no versions, show admin versions
            if not rows and company_id != _ADMIN_COMPANY_ID:
                rows = conn.execute(
                    "SELECT task, version, model_file, metrics, mapping, data_summary,"
                    " experiment, model_type, is_active, saved_at_utc"
                    " FROM model_versions"
                    " WHERE company_id = ? AND task = ?"
                    " ORDER BY saved_at_utc DESC",
                    (_ADMIN_COMPANY_ID, task),
                ).fetchall()
        finally:
            conn.close()

        return [self._row_to_dict(r) for r in rows]

    def activate(self, company_id: str, task: str, version: str) -> None:
        """Mark a specific version as active for live predictions.

        Deactivates any previously active version for the same (company, task).
        """
        conn = _get_db()
        try:
            # Verify the target version exists
            exists = conn.execute(
                "SELECT 1 FROM model_versions"
                " WHERE company_id = ? AND task = ? AND version = ?",
                (safe_company_id(company_id), task, version),
            ).fetchone()
            if exists is None:
                raise FileNotFoundError("Model version not found.")

            # Deactivate all versions for this (company, task)
            conn.execute(
                "UPDATE model_versions SET is_active = 0"
                " WHERE company_id = ? AND task = ?",
                (safe_company_id(company_id), task),
            )
            # Activate the selected version
            conn.execute(
                "UPDATE model_versions SET is_active = 1"
                " WHERE company_id = ? AND task = ? AND version = ?",
                (safe_company_id(company_id), task, version),
            )
            conn.commit()
        finally:
            conn.close()

    def list_companies(self) -> list[str]:
        """Return sorted list of company IDs that have data on disk."""
        return sorted(
            [p.name for p in self.root.iterdir() if p.is_dir()]
        )

    # -- JSON migration from pre-SQLite layout ------------------------------

    def migrate_from_json(self, company_id: str, task: str) -> int:
        """Import existing metadata_*.json files into SQLite.

        Called once per (company, task) during startup.  Returns the number
        of versions imported.  Idempotent -- already-imported versions are
        skipped (UNIQUE constraint).
        """
        task_dir = self._task_dir(company_id, task)
        count = 0
        conn = _get_db()
        try:
            for json_path in sorted(task_dir.glob("metadata_*.json")):
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue

                stamp = data.get("version", json_path.stem.replace("metadata_", ""))
                model_file = data.get("model_file", "")

                # Skip if already imported
                exists = conn.execute(
                    "SELECT 1 FROM model_versions"
                    " WHERE company_id = ? AND task = ? AND version = ?",
                    (safe_company_id(company_id), task, stamp),
                ).fetchone()
                if exists is not None:
                    continue

                conn.execute(
                    "INSERT OR IGNORE INTO model_versions"
                    " (company_id, task, version, model_file, metrics, mapping,"
                    "  data_summary, experiment, model_type, is_active, saved_at_utc)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                    (
                        safe_company_id(company_id),
                        task,
                        stamp,
                        model_file,
                        json.dumps(data.get("metrics", {}), ensure_ascii=False),
                        json.dumps(data.get("mapping"), ensure_ascii=False)
                        if data.get("mapping") is not None
                        else None,
                        json.dumps(data.get("data_summary"), ensure_ascii=False)
                        if data.get("data_summary") is not None
                        else None,
                        data.get("experiment"),
                        data.get("model_type"),
                        data.get("saved_at_utc", stamp),
                    ),
                )
                count += 1
            conn.commit()
        finally:
            conn.close()
        return count

    # -- Internal helpers ----------------------------------------------------

    @staticmethod
    def _row_to_dict(row: tuple) -> dict:
        """Convert a database row to the metadata dict format expected by callers."""
        (
            task, version, model_file, metrics_json, mapping_json,
            summary_json, experiment, model_type, is_active, saved_at,
        ) = row
        return {
            "task": task,
            "version": version,
            "model_file": model_file,
            "metrics": json.loads(metrics_json) if metrics_json else {},
            "mapping": json.loads(mapping_json) if mapping_json else None,
            "data_summary": json.loads(summary_json) if summary_json else None,
            "experiment": experiment,
            "model_type": model_type,
            "is_active": bool(is_active),
            "saved_at_utc": saved_at,
        }
