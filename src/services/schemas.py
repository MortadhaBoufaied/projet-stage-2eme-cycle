from dataclasses import dataclass, asdict
from typing import Any
import pandas as pd
@dataclass(frozen=True)
class Field:
    name:str; dtype:str; required:bool; description:str; example:Any; minimum:float|None=None; maximum:float|None=None; accepted:tuple=(); used:bool=True
CREDIT_FIELDS=[Field('client_id','string',True,'Unique customer identifier','C-1001',used=False),Field('LIMIT_BAL','number',True,'Approved credit limit',100000,0),Field('AGE','integer',True,'Customer age',35,18,110),Field('EDUCATION','integer',True,'Education code',2,accepted=(0,1,2,3,4,5,6)),Field('MARRIAGE','integer',True,'Marital-status code',1,accepted=(0,1,2,3)),*[Field(f'PAY_{i}','integer',True,f'Repayment status period {i}',0,-2,9) for i in (0,2,3,4,5,6)],*[Field(f'BILL_AMT{i}','number',True,f'Bill amount period {i}',25000) for i in range(1,7)],*[Field(f'PAY_AMT{i}','number',True,f'Payment amount period {i}',3000,0) for i in range(1,7)]]
CREDIT_TARGET=Field('default_next_month','integer',True,'Observed default label',0,accepted=(0,1),used=False)
FORECAST_FIELDS=[Field('date','date',True,'Observation date','2026-01-01'),Field('store_id','string',True,'Store identifier','S001'),Field('product_id','string',True,'Product identifier','P001'),Field('category','string',False,'Product category','Groceries'),Field('region','string',False,'Business region','North'),Field('inventory_level','number',False,'Inventory available',200,0),Field('units_sold','number',True,'Observed units sold',80,0),Field('units_ordered','number',False,'Units ordered',90,0),Field('price','number',False,'Unit price',25.5,0)]
ALIASES={'Date':'date','Store ID':'store_id','Product ID':'product_id','Category':'category','Region':'region','Inventory Level':'inventory_level','Units Sold':'units_sold','Units Ordered':'units_ordered','Price':'price'}
def fields(task,training=False): return CREDIT_FIELDS+([CREDIT_TARGET] if training else []) if task=='credit' else FORECAST_FIELDS
def normalize(df,task):
    d=df.rename(columns=ALIASES).copy(); d.columns=[str(c).strip() for c in d.columns]; return d
def template(task): return pd.DataFrame(columns=[f.name for f in fields(task,False)])
def documentation(task): return pd.DataFrame([asdict(f) for f in fields(task,False)])
