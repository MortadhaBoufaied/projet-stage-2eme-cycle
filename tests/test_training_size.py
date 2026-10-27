import pandas as pd
from src.services.training_size import fit_to_requested_size,forecast_problem_mask,dataframe_size_bytes

def sample(n=1000):
 return pd.DataFrame({'date':pd.date_range('2020-01-01',periods=n,freq='D').astype(str),'store_id':['S']*n,'product_id':[f'P{i}' for i in range(n)],'units_sold':[10]*n,'inventory_level':[20]*n,'payload':['x'*500]*n})

def test_problem_rows_are_removed_before_random_reduction():
 df=sample();df.loc[0,'units_sold']=-1;df.loc[1,'date']='bad'
 out,report=fit_to_requested_size(df,.2,forecast_problem_mask(df))
 assert report['problem_rows_removed']==2
 assert (pd.to_numeric(out.units_sold)>=0).all()
 assert pd.to_datetime(out.date,errors='coerce').notna().all()
 assert report['random_rows_removed']>0
 assert dataframe_size_bytes(out)<=int(.2*1024*1024)

def test_admin_can_enter_non_predefined_decimal_size():
 df=sample(100)
 out,report=fit_to_requested_size(df,0.037,forecast_problem_mask(df))
 assert report['requested_mb']==0.037
 assert dataframe_size_bytes(out)<=int(.037*1024*1024)
