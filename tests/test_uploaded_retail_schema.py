import pandas as pd
from src.services.schema import FORECAST_FIELDS,suggest_mapping,apply_mapping,mapping_errors,validate_forecast

def test_selected_retail_file_is_trainable_without_weather_or_promotion():
 df=pd.read_csv('/mnt/data/retail_store_inventory-selected-columns.csv')
 mapping=suggest_mapping(df.columns,FORECAST_FIELDS)
 mapped=apply_mapping(df,mapping)
 assert not mapping_errors(mapping)
 assert not validate_forecast(mapped,True)
 assert mapping['date']=='Date'
 assert mapping['inventory_level']=='Inventory Level'
 assert mapping['promotions_holidays']==''
 assert mapping['weather_conditions']==''
