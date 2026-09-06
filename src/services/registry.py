from pathlib import Path
import shutil
import json
from datetime import datetime


class Registry:
    def __init__(self, base_dir="models"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _dir(self, task):
        task_dir = self.base_dir / task
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def create_version(self, task, metadata=None):
        version_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        version_dir = self._dir(task) / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        if metadata:
            with open(version_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        return version_id

    def save_metadata(self, task, version_id, metadata):
        version_dir = self._dir(task) / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        with open(version_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self, task, version_id):
        metadata_file = self._dir(task) / version_id / "metadata.json"

        if not metadata_file.exists():
            return {}

        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

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