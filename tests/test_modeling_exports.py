import pandas as pd,numpy as np
from src.services.modeling import train_credit
from src.services.schemas import CREDIT_FIELDS,CREDIT_TARGET

def data(n=250):
 rng=np.random.default_rng(42);d={}
 for f in CREDIT_FIELDS:
  if f.name=='client_id':d[f.name]=[str(i) for i in range(n)]
  elif f.name=='AGE':d[f.name]=rng.integers(18,80,n)
  elif f.name=='EDUCATION':d[f.name]=rng.integers(1,5,n)
  elif f.name=='MARRIAGE':d[f.name]=rng.integers(1,4,n)
  elif f.name.startswith('PAY_') and not f.name.startswith('PAY_AMT'):d[f.name]=rng.integers(-2,5,n)
  else:d[f.name]=np.abs(rng.normal(10000,3000,n))
 y=(d['PAY_0']>1).astype(int);d[CREDIT_TARGET.name]=y;return pd.DataFrame(d)
def test_training_split_and_comparison():
 runs,best=train_credit(data(),['Logistic Regression','XGBoost']);assert len(runs)==2 and best in runs and best['split']['method']=='stratified'
def test_filtered_download_semantics():
 d=pd.DataFrame({'risk_tier':['HIGH','LOW'],'risk_score':[.8,.1]});f=d[d.risk_tier=='HIGH'];csv=f.to_csv(index=False);assert 'LOW' not in csv and len(f)==1
