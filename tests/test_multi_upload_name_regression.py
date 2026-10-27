from pathlib import Path

def test_multiple_uploads_do_not_access_name_on_list():
    s=Path("src/ui/app.py").read_text(encoding="utf-8")
    forecast=s[s.index("Historical sales training CSV files"):s.index("else:\n st.title('Workspace guide')")]
    assert "f.name" not in forecast
    assert "for item in f" in forecast
    assert "Files received" in forecast

def test_payment_single_upload_still_uses_file_name():
    s=Path("src/ui/app.py").read_text(encoding="utf-8")
    payment=s[s.index("Labeled payment history CSV"):s.index("Historical sales training CSV files") ]
    assert "f.name" in payment
