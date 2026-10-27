import io
import pandas as pd
from src.services.training_file_manager import prepare_csv_uploads

def csv_file(start, rows=100):
    d=pd.DataFrame({"date":pd.date_range("2024-01-01",periods=rows),"units_sold":range(start,start+rows),"store_id":"s1"})
    b=io.BytesIO(d.to_csv(index=False).encode()); b.name=f"{start}.csv"; return b

def test_two_files_are_combined_and_randomly_reduced_to_target():
    df,r=prepare_csv_uploads([csv_file(0),csv_file(100)],target_bytes=2500,chunksize=25)
    assert r["source_files"]==2 and r["rows_read"]==200
    assert r["rows_removed"]>0 and r["rows_kept"]==len(df)
    assert r["estimated_training_bytes"]<=2500

def test_same_seed_produces_same_random_rows():
    a,_=prepare_csv_uploads([csv_file(0)],target_bytes=1200,seed=7,chunksize=20)
    b,_=prepare_csv_uploads([csv_file(0)],target_bytes=1200,seed=7,chunksize=20)
    assert a.equals(b)

def test_streamlit_limit_is_higher_than_managed_target():
    from pathlib import Path
    c=Path(".streamlit/config.toml").read_text()
    assert "maxUploadSize = 4096" in c
