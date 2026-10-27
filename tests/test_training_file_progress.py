from pathlib import Path

def source(): return Path("src/ui/app.py").read_text(encoding="utf-8")

def test_pretraining_file_management_progress_is_visible_for_both_models():
    s=source()
    assert "uploaded payment file is being managed before training" in s
    assert "uploaded revenue file is being managed before training" in s
    assert s.count("Pre-training file checks completed.") == 2
    assert s.count("st.progress(8,text='Receiving the uploaded file...')") == 2
    assert "Read **{len(df):,} rows**" in s

def test_training_progress_and_model_isolation_are_preserved():
    s=source()
    assert "Training payment-risk XGBoost model. Please wait..." in s
    assert "Training cashflow / revenue XGBoost model. Please wait..." in s
    assert "registry.save(company,'credit'" in s
    assert "registry.save(company,'forecast'" in s
