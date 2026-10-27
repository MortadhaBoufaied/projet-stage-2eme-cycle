from dataclasses import dataclass,asdict,field
import pandas as pd, numpy as np
from .schemas import fields,normalize
from .forecast_schema import normalize as fc_normalize, spec as fc_spec
@dataclass
class Issue:
    level:str; code:str; column:str; message:str; count:int=0
@dataclass
class Report:
    valid:bool; rows:int; columns:int; duplicates:int; missing_cells:int; issues:list; kind:str|None=None
    def dict(self): return {**asdict(self),'issues':[asdict(x) for x in self.issues]}
    @property
    def errors(self): return [x for x in self.issues if getattr(x, 'level', None) == 'error']
def validate(df,task,training=False):
    d=normalize(df,task); issues=[]; fs=fields(task,training); expected={f.name for f in fs}; required={f.name for f in fs if f.required}
    missing=sorted(required-set(d.columns))
    for c in missing: issues.append(Issue('error','missing_column',c,f'Required column {c} is missing. Download the current template.'))
    for f in fs:
        if f.name not in d: continue
        s=d[f.name]; n=int(s.isna().sum())
        if n and f.required: issues.append(Issue('error','missing_value',f.name,f'{f.name} contains {n} missing required values.',n))
        if f.dtype in ('number','integer'):
            x=pd.to_numeric(s,errors='coerce'); bad=int((x.isna()&s.notna()).sum())
            if bad: issues.append(Issue('error','invalid_number',f.name,f'{f.name} contains {bad} non-numeric values.',bad))
            if f.minimum is not None:
                k=int((x<f.minimum).sum());
                if k: issues.append(Issue('error','below_minimum',f.name,f'{f.name} contains {k} values below {f.minimum}.',k))
            if f.maximum is not None:
                k=int((x>f.maximum).sum());
                if k: issues.append(Issue('error','above_maximum',f.name,f'{f.name} contains {k} values above {f.maximum}.',k))
            if f.accepted:
                k=int((~x.isin(f.accepted)&x.notna()).sum());
                if k: issues.append(Issue('error','invalid_category',f.name,f'{f.name} contains {k} values outside {list(f.accepted)}.',k))
        elif f.dtype=='date':
            x=pd.to_datetime(s,errors='coerce'); bad=int((x.isna()&s.notna()).sum())
            if bad: issues.append(Issue('error','invalid_date',f.name,f'{f.name} contains {bad} invalid dates.',bad))
    dup=int(d.duplicated().sum())
    if dup: issues.append(Issue('warning','duplicates','',f'{dup} duplicate rows were detected.',dup))
    if len(d)==0: issues.append(Issue('error','empty','','The dataset is empty.'))
    if training and len(d)<100: issues.append(Issue('error','insufficient_rows','',f'Training needs at least 100 rows; received {len(d)}.'))
    return d,Report(not any(x.level=='error' for x in issues),len(d),len(d.columns),dup,int(d.isna().sum().sum()),issues)

def validate_forecast(df, training=False):
    """Validate a forecast dataset, auto-detecting weekly_combined vs daily_retail."""
    d, kind = fc_normalize(df)
    s = fc_spec(kind)
    issues = []
    required = s['required']
    missing = sorted(set(required) - set(d.columns))
    for c in missing:
        issues.append(Issue('error', 'missing_column', c, f'Required column {c} is missing.'))
    for col in required:
        if col not in d.columns:
            continue
        n = int(d[col].isna().sum())
        if n:
            issues.append(Issue('error', 'missing_value', col, f'{col} contains {n} missing values.', n))
    date_col = s.get('date', 'date')
    if date_col in d.columns:
        x = pd.to_datetime(d[date_col], errors='coerce')
        bad = int((x.isna() & d[date_col].notna()).sum())
        if bad:
            issues.append(Issue('error', 'invalid_date', date_col, f'{date_col} contains {bad} invalid dates.', bad))
    target = s.get('target')
    if target and target in d.columns:
        x = pd.to_numeric(d[target], errors='coerce')
        bad = int((x.isna() & d[target].notna()).sum())
        if bad:
            issues.append(Issue('error', 'invalid_number', target, f'{target} contains {bad} non-numeric values.', bad))
    dup = int(d.duplicated().sum())
    if dup:
        issues.append(Issue('warning', 'duplicates', '', f'{dup} duplicate rows detected.', dup))
    if len(d) == 0:
        issues.append(Issue('error', 'empty', '', 'The dataset is empty.'))
    if training and len(d) < 100:
        issues.append(Issue('error', 'insufficient_rows', '', f'Training needs at least 100 rows; received {len(d)}.'))
    valid = not any(x.level == 'error' for x in issues)
    return d, Report(valid, len(d), len(d.columns), dup, int(d.isna().sum().sum()), issues, kind=kind)
