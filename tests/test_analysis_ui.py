from pathlib import Path
def test_simple_analysis_ui():
 t=Path('src/ui/app.py').read_text();assert "multiselect('Filter by risk'" in t;assert "text_input('Search customer'" in t;assert "quality_report(df)" not in t[t.index("elif page=='Payment Risk Assessment Agent':"):t.index("elif page=='Review cases':")];assert 'suggestion' in t
