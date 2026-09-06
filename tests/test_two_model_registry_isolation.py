from pathlib import Path
import json
from src.services.model_registry import ModelRegistry

def test_payment_and_cashflow_status_are_strictly_isolated(tmp_path):
    r=ModelRegistry(tmp_path)
    credit=r._task_dir("company", "credit", True)
    forecast=r._task_dir("company", "forecast", True)
    (credit/"model_v1.joblib").write_bytes(b"model")
    (credit/"metadata_v1.json").write_text(json.dumps({"version":"v1","task":"credit","model_file":"model_v1.joblib","status":"CHAMPION"}))
    (credit/"active.json").write_text(json.dumps({"version":"v1","task":"credit","model_file":"model_v1.joblib","status":"CHAMPION"}))
    assert r.has_active_training("company", "credit") is True
    assert r.has_active_training("company", "forecast") is False
    assert r.versions("company", "forecast") == []

def test_wrong_task_metadata_is_ignored(tmp_path):
    r=ModelRegistry(tmp_path)
    forecast=r._task_dir("company", "forecast", True)
    (forecast/"metadata_bad.json").write_text(json.dumps({"version":"bad","task":"credit","model_file":"model_bad.joblib","status":"CHAMPION"}))
    (forecast/"active.json").write_text(json.dumps({"version":"bad","task":"credit","model_file":"model_bad.joblib","status":"CHAMPION"}))
    assert r.versions("company", "forecast") == []
    assert r.has_active_training("company", "forecast") is False
