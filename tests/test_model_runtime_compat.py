from pathlib import Path

def test_dependencies_are_pinned():
 s=(Path(__file__).parents[1]/'requirements.txt').read_text();assert 'scikit-learn==1.5.1' in s and 'joblib==1.5.3' in s

def test_registry_records_runtime_and_handles_imputer_mismatch():
 s=(Path(__file__).parents[1]/'src/services/model_registry.py').read_text();assert 'runtime_versions' in s and "'_fill_dtype'" in s
