from pathlib import Path
def test_final_ui():
 t=Path('src/ui/app.py').read_text();assert 'Filter by risk' in t and 'Search customer' in t and 'suggestion' in t;assert "page=='Model history'" not in t;assert 'Save trained model to server' in t
