import pandas as pd,numpy as np,io,json,secrets
from datetime import datetime,timezone
from pathlib import Path
from src.core.config import ANALYSES
from .registry import Registry
from .validation import normalize

def run(df,task,company):
 d=normalize(df);model,meta=Registry().active(task);X=d.copy()
 if task=='credit':
  ids=X.pop('client_id').astype(str) if 'client_id' in X else pd.Series(range(len(X))).astype(str);p=model.predict_proba(X[meta['features']])[:,1];tier=np.where(p>=.7,'High',np.where(p>=.4,'Medium','Low'));out=d.copy();out['risk_score']=p;out['risk_tier']=tier
 else:
  X=X.drop(columns=['date',meta.get('target','target_units_sold')],errors='ignore');out=d.copy();out['forecast_value']=np.maximum(0,model.predict(X[meta['features']]));out['stockout_risk']=pd.to_numeric(out.get('inventory_level',np.nan),errors='coerce')<out.forecast_value
 aid='an_'+secrets.token_hex(6);base=ANALYSES/company;base.mkdir(parents=True,exist_ok=True);out.to_csv(base/f'{aid}.csv',index=False);info={'analysis_id':aid,'company_id':company,'task':task,'model_version':meta['version_id'],'created_at':datetime.now(timezone.utc).isoformat(),'records':len(out)};(base/f'{aid}.json').write_text(json.dumps(info,indent=2));return out,info
def history(company):
 p=ANALYSES/company;return [json.loads(f.read_text()) for f in sorted(p.glob('*.json'),reverse=True)] if p.exists() else []
def csv_bytes(df):return df.to_csv(index=False).encode()
def excel_bytes(df):
 b=io.BytesIO();df.to_excel(b,index=False,engine='openpyxl');return b.getvalue()
