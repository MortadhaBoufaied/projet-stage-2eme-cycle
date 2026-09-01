from __future__ import annotations
from difflib import SequenceMatcher
import re
import pandas as pd

CREDIT_FEATURES = ["LIMIT_BAL", "AGE", "EDUCATION", "MARRIAGE"] + [f"PAY_{i}" for i in range(7)] + [f"BILL_AMT{i}" for i in range(1,7)] + [f"PAY_AMT{i}" for i in range(1,7)]
CREDIT_TARGET = "default_next_month"
CREDIT_ID = "client_id"
FORECAST_FIELDS = ["date","store_id","product_id","category","region","units_sold","inventory_level","promotions_holidays","weather_conditions"]

def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())

def suggest_mapping(columns, required):
    columns=list(columns); result={}; used=set()
    for canonical in required:
        ranked=sorted(((SequenceMatcher(None,_norm(canonical),_norm(c)).ratio(),c) for c in columns if c not in used), reverse=True)
        choice=ranked[0][1] if ranked and (ranked[0][0] >= .72 or _norm(canonical)==_norm(ranked[0][1])) else ""
        result[canonical]=choice
        if choice: used.add(choice)
    return result

def mapping_errors(mapping):
    selected=[v for v in mapping.values() if v]
    duplicates=sorted({v for v in selected if selected.count(v)>1})
    errors=[]
    if duplicates: errors.append("One source column cannot map to multiple fields: "+", ".join(duplicates))
    return errors

def apply_mapping(df: pd.DataFrame, mapping: dict[str,str]) -> pd.DataFrame:
    return df.rename(columns={source:canonical for canonical,source in mapping.items() if source}).copy()

def validate_credit(df, require_target=True):
    required=CREDIT_FEATURES+([CREDIT_TARGET] if require_target else [])
    errors=[f"Missing column: {c}" for c in required if c not in df.columns]
    if not errors:
        if require_target and len(df)<30: errors.append("Credit training data requires at least 30 rows.")
        if require_target:
            vals=set(pd.to_numeric(df[CREDIT_TARGET],errors='coerce').dropna().unique())
            if not vals.issubset({0,1}) or len(vals)<2: errors.append("The target must contain both binary classes 0 and 1.")
        ages=pd.to_numeric(df['AGE'],errors='coerce')
        if ((ages<18)|(ages>110)).any(): errors.append("AGE contains values outside 18 to 110.")
        limits=pd.to_numeric(df['LIMIT_BAL'],errors='coerce')
        if (limits<0).any(): errors.append("LIMIT_BAL cannot be negative.")
    return errors

def validate_forecast(df, require_target=True):
    required=FORECAST_FIELDS if require_target else [c for c in FORECAST_FIELDS if c!='units_sold']
    errors=[f"Missing column: {c}" for c in required if c not in df.columns]
    if not errors:
        dates=pd.to_datetime(df['date'],errors='coerce')
        if dates.isna().any(): errors.append("Some date values are invalid.")
        if dates.nunique()<10: errors.append("Forecast data requires at least 10 distinct dates.")
        keys=['date','store_id','product_id']
        if df.duplicated(keys).any(): errors.append("Duplicate date/store/product records were found.")
        if require_target and (pd.to_numeric(df['units_sold'],errors='coerce')<0).any(): errors.append("units_sold cannot be negative.")
    return errors

def quality_report(df):
    return {
        'rows':len(df),'columns':len(df.columns),'duplicate_rows':int(df.duplicated().sum()),
        'missing_cells':int(df.isna().sum().sum()),
        'missing_percent':round(float(df.isna().mean().mean()*100),2) if len(df.columns) else 0,
    }
