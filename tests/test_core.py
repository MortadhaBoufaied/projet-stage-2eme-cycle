import pandas as pd,tempfile
from src.services.schemas import template_bytes
from src.services.validation import validate
from src.ml.metrics import classification,regression
from src.services.analysis import csv_bytes

def test_template_headers():assert b'client_id' in template_bytes('credit') and b'store_id' in template_bytes('forecast')
def test_validation_missing():
 _,r=validate(pd.DataFrame({'x':[1]}),'credit');assert not r.valid and r.errors
def test_validation_age():
 row={'client_id':'1','LIMIT_BAL':1,'AGE':500,'EDUCATION':1,'MARRIAGE':1,**{f'PAY_{i}':0 for i in [0,2,3,4,5,6]},**{f'BILL_AMT{i}':1 for i in range(1,7)},**{f'PAY_AMT{i}':1 for i in range(1,7)}}
 _,r=validate(pd.DataFrame([row]*20),'credit');assert not r.valid
def test_metrics_safe():
 m=classification([0,0],[.1,.2]);assert m['roc_auc'] is None
 r=regression([0,1],[0,1]);assert r['wape']==0
def test_filtered_export():
    d=pd.DataFrame({"risk_tier":["High","Low"]})
    f=d[d.risk_tier=="High"]
    assert len(pd.read_csv(__import__("io").BytesIO(csv_bytes(f))))==1

def test_auth_coexists_with_legacy_eight_column_users(tmp_path, monkeypatch):
    import sqlite3
    import src.services.auth as auth
    legacy_db = tmp_path / "legacy.db"
    with sqlite3.connect(legacy_db) as connection:
        connection.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password TEXT, "
            "role TEXT, company TEXT, name TEXT, active INTEGER, created_at TEXT)"
        )
    monkeypatch.setattr(auth, "DB", legacy_db)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "ChangeMe123!")
    user = auth.login("ADMIN@EXAMPLE.COM", "ChangeMe123!")
    assert user is not None
    assert user["role"] == "admin"
    with sqlite3.connect(legacy_db) as connection:
        assert len(connection.execute("PRAGMA table_info(users)").fetchall()) == 8
        assert connection.execute("SELECT COUNT(*) FROM app_users").fetchone()[0] == 2
