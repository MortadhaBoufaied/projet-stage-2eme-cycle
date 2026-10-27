import tempfile
from pathlib import Path
import numpy as np,pandas as pd
from src.services.flexible_schema import analyze_dataframe
from src.services.dynamic_contract import schema_payload,prediction_template,validate_upload
from src.services.modeling import train_credit,train_forecast
from src.services.registry import Registry

def test_arbitrary_credit_columns_roundtrip():
    n=240;r=np.random.default_rng(4)
    d=pd.DataFrame({'invoice_ref':[f'I{i}' for i in range(n)],'amount_due':r.normal(500,80,n),'payment_terms':r.choice(['30D','60D'],n),'historical_late_rate':r.random(n)})
    d['late_outcome']=(d.historical_late_rate>.55).astype(int)
    s=analyze_dataframe(d);s.suggested_target='late_outcome';s.suggested_features=['amount_due','payment_terms','historical_late_rate'];s.suggested_ids=['invoice_ref']
    runs,best=train_credit(d,['Logistic Regression'],s.suggested_features,s.suggested_target);best['schema_contract']=schema_payload(s,d.columns);best['id_columns']=s.suggested_ids
    with tempfile.TemporaryDirectory() as td:
        reg=Registry(Path(td));vid=reg.save('credit',best,{},{});reg.activate('credit',vid);m,meta=reg.active('credit')
        assert list(prediction_template(meta).columns)==['invoice_ref','amount_due','payment_terms','historical_late_rate']
        aligned,report=validate_upload(d.drop(columns=['late_outcome']).head(8),meta);assert report['valid'];assert len(m.predict_proba(aligned[meta['features']]))==8

def test_arbitrary_forecast_columns_roundtrip():
    n=160;r=np.random.default_rng(8)
    d=pd.DataFrame({'period':pd.date_range('2025-01-01',periods=n),'department':r.choice(['A','B'],n),'sales_value':r.normal(1000,100,n),'campaign':r.choice(['yes','no'],n)})
    s=analyze_dataframe(d);s.suggested_target='sales_value';s.suggested_features=['period','department','campaign'];s.suggested_ids=[]
    # Datetimes need stable string representation in generic sklearn pipelines.
    d['period']=d.period.astype(str)
    runs,best=train_forecast(d,['Ridge'],s.suggested_features,s.suggested_target);best['schema_contract']=schema_payload(s,d.columns)
    assert best['features']==s.suggested_features

def test_legacy_one_hot_metadata_is_repaired_to_raw_features():
    n=180;r=np.random.default_rng(21)
    d=pd.DataFrame({'business_code':r.choice(['CA02','U001'],n),'invoice_currency':r.choice(['CAD','USD'],n),'amount':r.normal(100,10,n)})
    d['late']=(d.amount>100).astype(int)
    runs,best=train_credit(d,['Logistic Regression'],['business_code','invoice_currency','amount'],'late')
    with tempfile.TemporaryDirectory() as td:
        reg=Registry(Path(td));vid=reg.save('credit',best,{},{});reg.activate('credit',vid)
        meta=reg.load_metadata('credit',vid);meta['features']=['business_code_CA02','business_code_U001','invoice_currency_CAD','invoice_currency_USD','amount'];reg.save_metadata('credit',vid,meta)
        model,repaired=reg.active('credit')
        assert repaired['features']==['business_code','invoice_currency','amount']
        assert repaired['metadata_repaired_from_pipeline'] is True
