from pathlib import Path
import ast
from src.services.model_registry import ModelRegistry

class Dummy: pass

def test_ui_has_only_two_services():
    s=Path("src/ui/app.py").read_text(encoding="utf-8")
    ast.parse(s)
    assert "Cashflow / Revenue Forecast Agent" in s
    assert "Payment Risk Assessment Agent" in s
    assert "LendingClub" not in s and "loan profile" not in s.lower()

def test_training_status_is_independent_and_forget_exists(tmp_path):
    r=ModelRegistry(tmp_path)
    r.save("c","forecast",Dummy(),{"metrics":{}})
    assert r.has_training("c","forecast")
    assert not r.has_training("c","credit")
    assert r.has_active_training("c","forecast")
    assert not r.has_active_training("c","credit")
    assert r.forget_training("c","forecast")==1
    assert not r.has_training("c","forecast")

def test_active_training_status_stays_independent_in_both_directions(tmp_path):
    r=ModelRegistry(tmp_path)
    r.save("c","credit",Dummy(),{})
    assert r.has_active_training("c","credit")
    assert not r.has_active_training("c","forecast")
    r.save("c","forecast",Dummy(),{})
    assert r.has_active_training("c","credit")
    assert r.has_active_training("c","forecast")

def test_registry_rejects_third_task(tmp_path):
    r=ModelRegistry(tmp_path)
    try:r.versions("c","lending_club_default");assert False
    except ValueError:pass

def test_dark_buttons_have_light_text():
    s=Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "color:#ffffff!important" in s
    assert "pointer-events:auto!important" in s
