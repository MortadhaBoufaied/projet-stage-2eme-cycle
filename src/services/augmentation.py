from __future__ import annotations
import numpy as np
import pandas as pd
from src.config import RANDOM_STATE
from src.services.schema import CREDIT_FEATURES,CREDIT_TARGET,PAY_STATUS_FIELDS

DISCRETE=set(PAY_STATUS_FIELDS+["EDUCATION","MARRIAGE"])

def augment_credit_training_data(df,target_ratio=.75,jitter=.025,random_state=RANDOM_STATE):
    """Augment minority-class training rows only. Keeps holdout data untouched.
    Numeric continuous variables receive mild, scale-aware noise; discrete fields and target are copied exactly.
    """
    if not 0 < target_ratio <= 1: raise ValueError("target_ratio must be in (0, 1]")
    if not 0 <= jitter <= .15: raise ValueError("jitter must be between 0 and 0.15")
    y=pd.to_numeric(df[CREDIT_TARGET]).astype(int); counts=y.value_counts(); minority=int(counts.idxmin()); majority=int(counts.idxmax())
    desired=int(counts[majority]*target_ratio); needed=max(0,desired-int(counts[minority]))
    if needed==0:return df.copy(),{"original_rows":len(df),"augmented_rows":len(df),"synthetic_rows":0,"minority_class":minority,"target_ratio":target_ratio}
    rng=np.random.default_rng(random_state); minority_rows=df[y==minority]; selected=minority_rows.iloc[rng.integers(0,len(minority_rows),size=needed)].copy().reset_index(drop=True)
    for column in CREDIT_FEATURES:
        if column in DISCRETE: continue
        values=pd.to_numeric(df[column],errors="coerce"); scale=float(values.std()) if pd.notna(values.std()) else 0.
        base=pd.to_numeric(selected[column],errors="coerce"); selected[column]=base+rng.normal(0,max(scale*jitter,1e-9),needed)
        if column in {"LIMIT_BAL",*[f"BILL_AMT{i}" for i in range(1,7)],*[f"PAY_AMT{i}" for i in range(1,7)]}: selected[column]=selected[column].clip(lower=0)
    selected[CREDIT_TARGET]=minority
    if "client_id" in selected: selected["client_id"]=[f"AUG_{i+1:07d}" for i in range(needed)]
    result=pd.concat([df,selected],ignore_index=True).sample(frac=1,random_state=random_state).reset_index(drop=True)
    return result,{"original_rows":len(df),"augmented_rows":len(result),"synthetic_rows":needed,"minority_class":minority,"target_ratio":target_ratio,"jitter":jitter}
