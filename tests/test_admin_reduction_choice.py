import io
from pathlib import Path
import pandas as pd
from src.services import training_file_manager as m
def uploaded(rows=200):
 b=io.BytesIO(pd.DataFrame({"a":range(rows),"text":["long value"]*rows}).to_csv(index=False).encode());b.name="large.csv";return b
def test_actual_download_file_respects_admin_target(tmp_path,monkeypatch):
 monkeypatch.setattr(m,"CACHE_DIR",tmp_path)
 df,r,path=m.prepare_csv_uploads([uploaded()],10*1024*1024,chunksize=25)
 assert path.exists() and path.stat().st_size<=r["target_bytes"]
 assert r["actual_output_bytes"]==path.stat().st_size
def test_ui_asks_size_and_offers_download():
 s=Path("src/ui/app.py").read_text(encoding="utf-8")
 assert "Reduced file size" in s and "select_slider" in s
 assert "Download reduced training CSV" in s
 assert "actual_output_bytes" in s
