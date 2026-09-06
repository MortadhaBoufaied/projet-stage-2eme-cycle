from pathlib import Path
def test_precise_percentage_scale():
 t=Path('src/ui/app.py').read_text();assert "mul(100).round(2)" in t;assert "max_value=100.0" in t;assert "format='%.2f%%'" in t
