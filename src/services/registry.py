from pathlib import Path
import shutil
import json
import hashlib
from datetime import datetime, timezone
import numpy as np

import joblib

from src.config import ARTIFACTS


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


class Registry:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = ARTIFACTS / "models"
        else:
            self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _dir(self, task):
        task_dir = self.base_dir / task
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def create_version(self, task, metadata=None):
        now = datetime.now(timezone.utc)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        short_hash = hashlib.sha256(stamp.encode()).hexdigest()[:6]
        version_id = f"{stamp}_{short_hash}"

        version_dir = self._dir(task) / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        if metadata:
            with open(version_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        return version_id

    def save_metadata(self, task, version_id, metadata):
        version_dir = self._dir(task) / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        # Convert numpy types to JSON-serializable types
        metadata = convert_numpy_types(metadata)

        with open(version_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self, task, version_id):
        metadata_file = self._dir(task) / version_id / "metadata.json"

        if not metadata_file.exists():
            return {}

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If metadata file is corrupted, return empty dict
            return {}

    def list_versions(self, task):
        task_dir = self._dir(task)

        versions = []

        for p in task_dir.iterdir():
            if p.is_dir():
                versions.append(p.name)

        versions.sort(reverse=True)
        return versions

    def activate(self, task, version_id):
        active_file = self._dir(task) / "ACTIVE"
        active_file.write_text(version_id)

    def get_active(self, task):
        active_file = self._dir(task) / "ACTIVE"

        if active_file.exists():
            return active_file.read_text().strip()

        return None

    def delete(self, task, version_id):
        version_dir = self._dir(task) / version_id

        if version_dir.exists():
            shutil.rmtree(version_dir)

        active_file = self._dir(task) / "ACTIVE"

        if (
            active_file.exists()
            and active_file.read_text().strip() == version_id
        ):
            active_file.unlink()

    # ── High-level API expected by the UI ────────────────────────────

    def save(self, task, best_run, quality_report, assessment):
        """Save a trained model, its metadata, and assessment to a new version.

        Parameters
        ----------
        task : str
            'credit' or 'forecast'.
        best_run : dict
            Training result dict with keys like 'model', 'algorithm',
            'test', 'validation', etc.
        quality_report : dict
            Data-quality / validation report (stored for audit).
        assessment : dict
            AI-generated model assessment (strengths, weaknesses, etc.).

        Returns
        -------
        str
            The version_id of the newly created version.
        """
        now = datetime.now(timezone.utc)
        version_id = self.create_version(task)

        version_dir = self._dir(task) / version_id

        # Persist the model object
        model_obj = best_run.get('model')
        if model_obj is not None:
            joblib.dump(model_obj, version_dir / "model.joblib")

        # Build and persist metadata
        metadata = {
            "version_id": version_id,
            "task": task,
            "algorithm": best_run.get('algorithm', 'unknown'),
            "training_timestamp": now.isoformat(),
            "test_metrics": best_run.get('test', {}),
            "validation_metrics": best_run.get('validation', {}),
            "quality_report": quality_report if isinstance(quality_report, dict) else {},
            "assessment": assessment if isinstance(assessment, dict) else {},
            "features": best_run.get('features', []),
            "raw_features": best_run.get('raw_features') or [],
            "prediction_input_columns": best_run.get('prediction_input_columns') or best_run.get('raw_features') or [],
            "training_source_columns": best_run.get('training_source_columns') or [],
            "input_contract": best_run.get('input_contract') or [],
            "column_meanings": best_run.get('column_meanings') or {},
            "numeric_features": best_run.get('numeric_features', []),
            "categorical_features": best_run.get('categorical_features', []),
            "target": best_run.get('target'),
        }
        self.save_metadata(task, version_id, metadata)

        return version_id

    def active(self, task):
        """Load the active model and its metadata.

        Returns
        -------
        tuple[object, dict]
            (model_object, metadata_dict).

        Raises
        ------
        FileNotFoundError
            If no active version exists or the model file is missing.
        """
        version_id = self.get_active(task)
        if version_id is None:
            raise FileNotFoundError(f"No active {task} model.")

        version_dir = self._dir(task) / version_id
        if not version_dir.exists():
            raise FileNotFoundError(
                f"Active version directory missing: {version_id}"
            )

        meta = self.load_metadata(task, version_id)
        meta.setdefault("version_id", version_id)

        model_path = version_dir / "model.joblib"
        if model_path.exists():
            model_obj = joblib.load(model_path)
        else:
            model_obj = None

        return model_obj, meta

    def versions(self, task):
        """Return a list of metadata dicts for every saved version (newest first).

        Each dict contains at least 'version_id', 'algorithm', and
        'training_timestamp'.
        """
        result = []
        for vid in self.list_versions(task):
            meta = self.load_metadata(task, vid)
            meta.setdefault("version_id", vid)
            meta.setdefault("algorithm", "unknown")
            meta.setdefault("training_timestamp", "N/A")
            result.append(meta)
        return result
