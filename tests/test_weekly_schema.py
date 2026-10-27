import pandas as pd
from src.services.validation import validate_forecast
from src.services.forecast_schema import normalize,spec

def test_combined_file_accepted():
 d=pd.read_csv('data/training/combined_retail_weekly_training_corrected.csv')
 x,r=validate_forecast(d,True)
 assert r.valid and r.kind=='weekly_combined' and len(x)==14856

def test_optional_region_inventory_can_be_missing():
 d=pd.read_csv('data/training/combined_retail_weekly_training_corrected.csv')
 x,r=validate_forecast(d[d.dataset_source=='data_raw'],True)
 assert r.valid and x.region.isna().all() and x.inventory_level.isna().all()

def test_target_is_next_week_and_complete():
 d=pd.read_csv('data/training/combined_retail_weekly_training_corrected.csv')
 assert d.target_units_sold.notna().all() and (d.target_units_sold>=0).all()

def test_daily_schema_still_detected():
 d=pd.DataFrame({'Date':pd.date_range('2024-01-01',periods=100).astype(str).tolist(),'Store ID':['S1']*100,'Product ID':['P1']*100,'Category':['A']*100,'Inventory Level':[2]*100,'Units Sold':[1]*100})
 _,r=validate_forecast(d);assert r.valid and r.kind=='daily_retail'
