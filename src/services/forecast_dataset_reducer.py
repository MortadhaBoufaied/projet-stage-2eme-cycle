from __future__ import annotations
import math
import pandas as pd

def dataframe_size_bytes(df):return int(df.memory_usage(index=True,deep=True).sum())
def forecast_problem_mask(df):
 bad=pd.Series(False,index=df.index)
 for c in ('date','store_id','product_id','units_sold'):
  if c not in df:return pd.Series(True,index=df.index)
  bad|=df[c].isna()|df[c].astype(str).str.strip().eq('')
 bad|=pd.to_datetime(df.date,errors='coerce').isna()
 sold=pd.to_numeric(df.units_sold,errors='coerce');bad|=sold.isna()|(sold<0)
 if 'inventory_level' in df:
  stock=pd.to_numeric(df.inventory_level,errors='coerce');bad|=stock.isna()|(stock<0)
 bad|=df.duplicated(['date','store_id','product_id'],keep='last')
 return bad
def prepare_forecast_dataset(df,requested_mb):
 requested_mb=float(requested_mb)
 if not math.isfinite(requested_mb) or requested_mb<=0:raise ValueError('Requested size must be greater than 0 MB.')
 limit=int(requested_mb*1024*1024);source_rows=len(df);bad=forecast_problem_mask(df);clean=df.loc[~bad].copy()
 clean=clean.assign(_date=pd.to_datetime(clean.date,errors='coerce')).sort_values(['store_id','product_id','_date'],kind='stable')
 removed_for_size=0
 if dataframe_size_bytes(clean)>limit and len(clean):
  keep=max(1,int(len(clean)*limit/dataframe_size_bytes(clean)))
  while keep>=1:
   groups=list(clean.groupby(['store_id','product_id'],sort=False,dropna=False));pieces=[]
   for _,group in groups:
    amount=max(1,int(round(keep*len(group)/len(clean))));pieces.append(group.tail(min(amount,len(group))))
   candidate=pd.concat(pieces).tail(keep)
   if dataframe_size_bytes(candidate)<=limit:clean=candidate;break
   keep=max(1,keep-1)
  removed_for_size=int((~bad).sum()-len(clean))
 clean=clean.sort_values('_date',kind='stable').drop(columns=['_date']).reset_index(drop=True)
 return clean,{'requested_mb':requested_mb,'prepared_mb':round(dataframe_size_bytes(clean)/1024/1024,2),'source_rows':source_rows,'prepared_rows':len(clean),'problem_rows_removed':int(bad.sum()),'valid_rows_removed_for_size':removed_for_size}
