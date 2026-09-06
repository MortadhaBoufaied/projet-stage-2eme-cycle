import pandas as pd, numpy as np
from pathlib import Path
from src.services.schemas import template,documentation,CREDIT_FIELDS,CREDIT_TARGET
from src.services.validation import validate
from src.services.metrics import classification,regression
from src.services.intelligence import deterministic

def credit(n=150):
 rng=np.random.default_rng(1);d={f.name:rng.normal(10,2,n) for f in CREDIT_FIELDS if f.name not in ('client_id','AGE','EDUCATION','MARRIAGE')};d['client_id']=[f'C{i}' for i in range(n)];d['AGE']=rng.integers(18,80,n);d['EDUCATION']=rng.integers(1,5,n);d['MARRIAGE']=rng.integers(1,4,n)
 for c in [x for x in d if x.startswith('PAY_')]: d[c]=rng.integers(-2,5,n)
 d[CREDIT_TARGET.name]=rng.integers(0,2,n);return pd.DataFrame(d)
def test_templates_are_empty_and_documented():
 assert template('credit').empty and template('forecast').empty
 assert len(documentation('credit'))>20
def test_validation_missing_columns_and_empty():
 _,r=validate(pd.DataFrame(),'credit',False);assert not r.valid and any(i.code=='empty' for i in r.issues)
def test_credit_validation_all_rows():
 d=credit();d.loc[149,'AGE']=999;_,r=validate(d,'credit',True);assert not r.valid and any(i.column=='AGE' for i in r.issues)
def test_duplicates_warning():
 d=credit();d=pd.concat([d,d.iloc[[0]]]);_,r=validate(d,'credit',True);assert r.duplicates==1
def test_safe_classification_single_class():
 m=classification([0,0,0],[.1,.2,.3]);assert m['ROC-AUC'] is None and m['PR-AUC'] is None
def test_regression_metrics():
 m=regression([10,20],[11,18]);assert m['MAE']==1.5 and m['RMSE']>0
def test_slm_fallback_governance():
 x=deterministic('credit',{'Recall':.4,'Precision':.5,'ROC-AUC':.7},{'duplicates':0});assert x['generator']=='deterministic fallback' and 'evidence_used' in x and 'human_review_notice' in x
