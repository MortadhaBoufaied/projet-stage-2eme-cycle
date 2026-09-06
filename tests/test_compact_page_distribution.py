from pathlib import Path

def test_dense_page_layout_is_applied_after_sidebar_theme():
    s=Path("src/ui/app.py").read_text(encoding="utf-8")
    for rule in [
        ".main .block-container{max-width:1480px",
        ".hero,.app-hero{padding:.9rem 1.25rem",
        "font-size:1.68rem",
        "min-height:84px",
        "gap:.72rem",
    ]:
        assert rule in s
    assert s.index("/* Compact page rhythm") > s.index("/* Kaggle-inspired navigation shell")

def test_training_content_and_two_model_status_remain_present():
    s=Path("src/ui/app.py").read_text(encoding="utf-8")
    assert "Train platform models" in s
    assert "Payment Risk Assessment" in s
    assert "Cashflow / Revenue Forecast" in s
    assert "registry.has_active_training(company,'credit')" in s
    assert "registry.has_active_training(company,'forecast')" in s
