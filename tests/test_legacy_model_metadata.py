import json
from pathlib import Path
from src.services.model_registry import ModelRegistry,normalize_model_metadata

def test_legacy_metadata_gets_safe_defaults():
 item=normalize_model_metadata({"model_file":"model_abc.joblib","saved_at_utc":"2025-01-01"},"credit")
 assert item["version"]=="abc"
 assert item["status"]=="ARCHIVED"
 assert item["created_at_utc"]=="2025-01-01"

def test_versions_accept_metadata_without_status(tmp_path):
 d=tmp_path/"company"/"credit";d.mkdir(parents=True)
 (d/"metadata_old.json").write_text(json.dumps({"model_file":"model_old.joblib","saved_at_utc":"2024-01-01"}))
 versions=ModelRegistry(tmp_path).versions("company","credit")
 assert versions[0]["status"]=="ARCHIVED" and versions[0]["version"]=="old"
