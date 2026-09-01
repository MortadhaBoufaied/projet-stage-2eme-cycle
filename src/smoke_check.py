import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from src.services.training import train_credit,train_forecast
from src.services.model_registry import ModelRegistry

def credit_data(n=240):
    rng=np.random.default_rng(42); d={'client_id':[f'C{i}' for i in range(n)],'LIMIT_BAL':rng.integers(10000,300000,n),'AGE':rng.integers(21,70,n),'EDUCATION':rng.integers(1,5,n),'MARRIAGE':rng.integers(1,4,n)}
    for i in range(7): d[f'PAY_{i}']=rng.integers(-2,5,n)
    for i in range(1,7): d[f'BILL_AMT{i}']=rng.integers(0,200000,n); d[f'PAY_AMT{i}']=rng.integers(0,50000,n)
    d['default_next_month']=(d['PAY_0']>1).astype(int); return pd.DataFrame(d)
def forecast_data():
    rows=[]
    for day,date in enumerate(pd.date_range('2025-01-01',periods=80)):
        rows.append({'date':date,'store_id':'S1','product_id':'P1','category':'Grocery','region':'North','units_sold':100+day%7,'inventory_level':500,'promotions_holidays':0,'weather_conditions':'Sunny'})
    return pd.DataFrame(rows)
def main():
    c,m=train_credit(credit_data(),'baseline'); assert m['n_test']>0
    f,m2=train_forecast(forecast_data(),'baseline'); assert m2['n_test']>0
    with tempfile.TemporaryDirectory() as td:
        r=ModelRegistry(Path(td)); r.save('demo','credit',c,{'metrics':m}); loaded,meta=r.load_latest('demo','credit'); assert meta['task']=='credit'
    print('Smoke check passed',m['ROC_AUC'],m2['MAE'])
if __name__=='__main__': main()
