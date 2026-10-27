from pathlib import Path
import inspect
from src.services.flexible_schema import slm_schema_suggestion, enhance_schema_with_slm, enhance_schema_with_slm_forecast

def test_column_meanings_supported_by_slm_schema_pipeline():
    assert 'column_meanings' in inspect.signature(slm_schema_suggestion).parameters
    assert 'column_meanings' in inspect.signature(enhance_schema_with_slm).parameters
    assert 'column_meanings' in inspect.signature(enhance_schema_with_slm_forecast).parameters

def test_meanings_editor_appears_before_confirm_schema_for_both_tasks():
    source=Path('src/ui/app.py').read_text(encoding='utf-8')
    meaning_positions=[]; start=0
    marker="st.markdown('#### Optional Column Meanings')"
    while True:
        pos=source.find(marker,start)
        if pos<0: break
        meaning_positions.append(pos); start=pos+1
    confirm_positions=[]; start=0
    marker2="st.markdown('#### Confirm Schema')"
    while True:
        pos=source.find(marker2,start)
        if pos<0: break
        confirm_positions.append(pos); start=pos+1
    assert len(meaning_positions)==len(confirm_positions)==2
    assert all(m<c for m,c in zip(meaning_positions,confirm_positions))
