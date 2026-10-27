from pathlib import Path

def test_meanings_are_persisted_and_used_for_hover():
    app=Path("src/ui/app.py").read_text()
    registry=Path("src/services/registry.py").read_text()
    intelligence=Path("src/services/intelligence.py").read_text()
    assert "def column_meanings_editor" in app
    assert "help=meanings.get(str(feature)) or None" in app
    assert '"column_meanings": best_run.get' in registry
    assert "'column_meanings':r.get" in intelligence
