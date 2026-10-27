import pandas as pd
DAILY_ALIASES={'Date':'date','Store ID':'store_id','Product ID':'product_id','Category':'category','Region':'region','Inventory Level':'inventory_level','Units Sold':'units_sold','Units Ordered':'units_ordered','Price':'price','Demand Forecast':'existing_demand_forecast'}
WEEKLY_REQUIRED=['dataset_source','date','store_id','product_id','units_sold','target_units_sold']
DAILY_REQUIRED=['date','store_id','product_id','category','inventory_level','units_sold']
def normalize(df):
 d=df.rename(columns=DAILY_ALIASES).copy();d.columns=[str(c).strip().lower() for c in d.columns]
 kind='weekly_combined' if 'target_units_sold' in d.columns else 'daily_retail'
 return d,kind
def spec(kind):
 if kind=='weekly_combined':return {'required':WEEKLY_REQUIRED,'target':'target_units_sold','date':'date','series':['dataset_source','store_id','product_id'],'optional':['category','category_detail','region','price','promotion_visibility','vendor_id','color','inventory_level','units_ordered_weekly'],'description':'Combined weekly next-period forecasting'}
 return {'required':DAILY_REQUIRED,'target':'units_sold','date':'date','series':['store_id','product_id'],'optional':['region','price','units_ordered','existing_demand_forecast'],'description':'Daily retail same-file forecasting'}
