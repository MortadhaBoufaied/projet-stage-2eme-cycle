import pandas as pd
from src.services.forecast_dataset_reducer import prepare_forecast_dataset,dataframe_size_bytes

def data(n=1500):
 return pd.DataFrame({'date':pd.date_range('2020-01-01',periods=n,freq='D').astype(str),'store_id':['S1']*n,'product_id':['P1']*n,'units_sold':[10]*n,'inventory_level':[20]*n,'payload':['x'*400]*n})

def test_single_dataset_reduction_removes_problems_first_and_honors_exact_size():
 df=data();df.loc[0,'date']='invalid';df.loc[1,'units_sold']=-1
 out,report=prepare_forecast_dataset(df,0.25)
 assert report['problem_rows_removed']==2
 assert report['valid_rows_removed_for_size']>0
 assert dataframe_size_bytes(out)<=int(0.25*1024*1024)
 assert pd.to_datetime(out.date,errors='coerce').notna().all()

def test_recent_continuous_history_is_preferred():
 df=data(500)
 out,_=prepare_forecast_dataset(df,0.08)
 assert out.date.max()==df.date.max()
 assert out.date.is_monotonic_increasing

def test_decimal_size_is_not_predefined():
 out,report=prepare_forecast_dataset(data(200),0.037)
 assert report['requested_mb']==0.037
 assert dataframe_size_bytes(out)<=int(0.037*1024*1024)
