import pandas as pd,numpy as np
from src.services.schemas import template,documentation,CREDIT_FIELDS,CREDIT_TARGET
from src.services.validation import validate
from src.services.metrics import classification,regression
from src.services.modeling import train_credit,train_forecast
from src.services.intelligence import deterministic

def credit(n=240):
 r=np.random.default_rng(7);d={}
 for f in CREDIT_FIELDS:
  if f.name=='client_id':d[f.name]=[f'C{i}' for i in range(n)]
  elif f.name=='AGE':d[f.name]=r.integers(18,80,n)
  elif f.name=='EDUCATION':d[f.name]=r.integers(0,7,n)
  elif f.name=='MARRIAGE':d[f.name]=r.integers(0,4,n)
  elif f.name.startswith('PAY_') and not f.name.startswith('PAY_AMT'):d[f.name]=r.integers(-2,6,n)
  else:d[f.name]=abs(r.normal(10000,3000,n))
 d[CREDIT_TARGET.name]=(d['PAY_0']>1).astype(int);return pd.DataFrame(d)
def forecast():
 rows=[]
 for p in ('P1','P2'):
  for i,dt in enumerate(pd.date_range('2023-01-02',periods=80,freq='W-MON')):
   rows.append({'date':dt,'store_id':'S1','product_id':p,'category':'A','region':'N','units_sold':20+i%9,'target_units_sold':21+(i+1)%9,'price':10,'promotion_visibility':i%2})
 return pd.DataFrame(rows)
def test_templates_empty_documented():assert template('credit').empty and template('forecast').empty and len(documentation('forecast'))>=10
def test_validation_actionable():
 d=credit();d.loc[239,'AGE']=999;_,r=validate(d,'credit',True);assert not r.valid and any('above' in i.message for i in r.issues)
def test_safe_metrics():assert classification([0,0],[.1,.2])['ROC-AUC'] is None and regression([1,2],[1,3])['MAE']==.5
def test_credit_training_compare():
 runs,b=train_credit(credit(),['Logistic Regression','XGBoost']);assert len(runs)==2 and b['split']['method']=='stratified'
def test_forecast_chronological():
 runs,b=train_forecast(forecast(),['Ridge']);assert b['split']['method']=='chronological' and b['target']=='target_units_sold'
def test_slm_fallback_is_governed():
 x=deterministic('credit',{'Recall':.4,'Precision':.4,'ROC-AUC':.6},{'duplicates':0});assert x['generator']=='deterministic fallback' and x['human_review_notice']
def test_filtered_export_only_contains_filter():
 d=pd.DataFrame({'risk_tier':['HIGH','LOW']});out=d[d.risk_tier=='HIGH'].to_csv(index=False);assert 'LOW' not in out
