from __future__ import annotations
import json,sqlite3,secrets
from datetime import datetime,timezone
from src.config import PROJECT_ROOT
DB=PROJECT_ROOT/'data'/'workspace.db'
def _connect():
 DB.parent.mkdir(parents=True,exist_ok=True);con=sqlite3.connect(DB);con.row_factory=sqlite3.Row
 con.executescript('''CREATE TABLE IF NOT EXISTS analyses(id TEXT PRIMARY KEY,company_id TEXT NOT NULL,file_name TEXT,rows INTEGER,high_count INTEGER,review_count INTEGER,standard_count INTEGER,created_at TEXT NOT NULL,result_json TEXT NOT NULL);CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY,analysis_id TEXT NOT NULL,company_id TEXT NOT NULL,client_id TEXT NOT NULL,risk_score REAL NOT NULL,risk_tier TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'OPEN',decision TEXT NOT NULL DEFAULT '',reason TEXT NOT NULL DEFAULT '',updated_at TEXT NOT NULL);''');return con
def save_analysis(company_id,file_name,result):
 aid='ana_'+secrets.token_hex(8);now=datetime.now(timezone.utc).isoformat();tiers=result['risk_tier'];high=int((tiers=='HIGH_RISK').sum());review=int((tiers=='MEDIUM_RISK').sum());standard=int((tiers=='LOW_RISK').sum())
 with _connect() as con:
  con.execute('INSERT INTO analyses VALUES(?,?,?,?,?,?,?,?,?)',(aid,company_id,file_name,len(result),high,review,standard,now,result.to_json(orient='records')))
  for row in result[result.risk_tier!='LOW_RISK'].itertuples():con.execute('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?)',('case_'+secrets.token_hex(8),aid,company_id,str(row.client_id),float(row.risk_score),row.risk_tier,'OPEN','','',now))
 return aid
def analyses(company_id):
 with _connect() as con:return [dict(r) for r in con.execute('SELECT id,file_name,rows,high_count,review_count,standard_count,created_at FROM analyses WHERE company_id=? ORDER BY created_at DESC',(company_id,))]
def cases(company_id,status='ALL'):
 sql='SELECT * FROM cases WHERE company_id=?';args=[company_id]
 if status!='ALL':sql+=' AND status=?';args.append(status)
 sql+=' ORDER BY risk_score DESC'
 with _connect() as con:return [dict(r) for r in con.execute(sql,args)]
def update_case(company_id,case_id,status,decision,reason):
 if status not in {'OPEN','REVIEWED','CLOSED'}:raise ValueError('Invalid case status')
 with _connect() as con:con.execute('UPDATE cases SET status=?,decision=?,reason=?,updated_at=? WHERE id=? AND company_id=?',(status,decision.strip(),reason.strip(),datetime.now(timezone.utc).isoformat(),case_id,company_id))
