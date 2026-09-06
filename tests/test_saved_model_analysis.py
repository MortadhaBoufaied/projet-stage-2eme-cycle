from pathlib import Path
def test_saved_model_analysis_controls_exist():
 text=Path('src/ui/app.py').read_text()
 assert 'Use this model to analyze a file' in text
 assert "registry.load_version(company,task,selection)" in text
 assert 'loan profile' not in text.lower()
