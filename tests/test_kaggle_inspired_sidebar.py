from pathlib import Path

def source(): return Path("src/ui/app.py").read_text(encoding="utf-8")

def test_sidebar_uses_clean_reference_inspired_design_without_create_button():
    s=source()
    assert "sidebar-brand" in s and "sidebar-accent:#20b2f2" in s
    assert "sidebar-active:#f1f3f4" in s and "border-left-color:#202124" in s
    sidebar=s[s.index("with st.sidebar:"):s.index("if admin_view and page=='Dashboard':")]
    assert "Create" not in sidebar and "Kaggle" not in sidebar

def test_navigation_values_are_preserved_for_routing():
    s=source()
    for page in ["Dashboard","Companies","Cashflow / Revenue Forecast Agent","Payment Risk Assessment Agent","Train models"]:
        assert repr(page) in s
    assert "format_func=nav_label" in s
