from __future__ import annotations
import math
import numpy as np
import pandas as pd

RANDOM_STATE = 42


def dataframe_size_bytes(df: pd.DataFrame) -> int:
    return int(df.memory_usage(index=True, deep=True).sum())


def forecast_problem_mask(df: pd.DataFrame) -> pd.Series:
    """Flag rows that are unsafe or unusable for forecast training."""
    mask=pd.Series(False,index=df.index)
    required=['date','store_id','product_id','units_sold']
    for col in required:
        if col not in df:
            return pd.Series(True,index=df.index)
        mask |= df[col].isna() | df[col].astype(str).str.strip().eq('')
    mask |= pd.to_datetime(df['date'],errors='coerce').isna()
    units=pd.to_numeric(df['units_sold'],errors='coerce')
    mask |= units.isna() | (units < 0)
    if 'inventory_level' in df:
        inventory=pd.to_numeric(df['inventory_level'],errors='coerce')
        mask |= inventory.isna() | (inventory < 0)
    mask |= df.duplicated(['date','store_id','product_id'],keep='first')
    return mask


def fit_to_requested_size(df: pd.DataFrame, requested_mb: float, problem_mask=None, random_state: int=RANDOM_STATE):
    """Remove problem rows first, then reproducibly sample valid rows to the requested in-memory size.

    The result is at or below the requested size. Sampling is random but reproducible.
    """
    if not math.isfinite(float(requested_mb)) or float(requested_mb) <= 0:
        raise ValueError('Requested training size must be greater than 0 MB.')
    requested_bytes=int(float(requested_mb)*1024*1024)
    source_bytes=dataframe_size_bytes(df)
    if problem_mask is None:
        problem_mask=pd.Series(False,index=df.index)
    problem_mask=pd.Series(problem_mask,index=df.index).fillna(True).astype(bool)
    clean=df.loc[~problem_mask].copy()
    removed_problem=int(problem_mask.sum())
    clean_bytes=dataframe_size_bytes(clean)
    randomly_removed=0
    if clean_bytes > requested_bytes and len(clean):
        bytes_per_row=max(clean_bytes/len(clean),1)
        keep=max(1,min(len(clean),int(requested_bytes/bytes_per_row)))
        # Refine until deep memory is at or below the administrator's request.
        while keep > 1:
            sampled=clean.sample(n=keep,random_state=random_state).copy()
            actual=dataframe_size_bytes(sampled)
            if actual <= requested_bytes:
                clean=sampled
                break
            keep=max(1,int(keep*requested_bytes/actual)-1)
        randomly_removed=int((~problem_mask).sum()-len(clean))
    clean=clean.sort_values([c for c in ['date','store_id','product_id'] if c in clean],kind='stable').reset_index(drop=True)
    return clean,{
        'requested_mb':float(requested_mb),'source_mb':round(source_bytes/1024/1024,2),
        'final_mb':round(dataframe_size_bytes(clean)/1024/1024,2),'source_rows':int(len(df)),
        'final_rows':int(len(clean)),'problem_rows_removed':removed_problem,
        'random_rows_removed':randomly_removed,'random_state':random_state,
    }
