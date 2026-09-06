from __future__ import annotations
import re
import pandas as pd


def _norm(value):
    return re.sub(r'[^a-z0-9]+','',str(value).strip().lower())


def _kind(series: pd.Series) -> str:
    non_null=series.dropna()
    if non_null.empty:return 'empty'
    if pd.to_numeric(non_null,errors='coerce').notna().mean()>=.95:return 'numeric'
    if pd.to_datetime(non_null,errors='coerce').notna().mean()>=.95:return 'datetime'
    return 'text'


def inspect_architecture(named_frames):
    """Require the same normalized columns and compatible data kinds before combining files."""
    if not named_frames:raise ValueError('Upload at least one training file.')
    reports=[]
    reference_name,reference=named_frames[0]
    reference_columns={_norm(c):str(c) for c in reference.columns}
    reference_kinds={_norm(c):_kind(reference[c]) for c in reference.columns}
    compatible=True
    for name,frame in named_frames:
        columns={_norm(c):str(c) for c in frame.columns}
        kinds={_norm(c):_kind(frame[c]) for c in frame.columns}
        missing=sorted(reference_columns[key] for key in reference_columns.keys()-columns.keys())
        extra=sorted(columns[key] for key in columns.keys()-reference_columns.keys())
        type_mismatches=[]
        for key in reference_columns.keys() & columns.keys():
            left,right=reference_kinds[key],kinds[key]
            if left!='empty' and right!='empty' and left!=right:
                type_mismatches.append(f'{columns[key]}: expected {left}, found {right}')
        valid=not missing and not extra and not type_mismatches
        compatible &= valid
        reports.append({'file':name,'rows':int(len(frame)),'columns':int(len(frame.columns)),
                        'compatible':bool(valid),'missing_columns':missing,'extra_columns':extra,
                        'type_mismatches':type_mismatches})
    return compatible,reports,reference_columns


def combine_compatible_files(named_frames):
    compatible,reports,reference_columns=inspect_architecture(named_frames)
    if not compatible:
        raise ValueError('Uploaded training files do not have the same architecture.')
    ordered=list(reference_columns.values())
    prepared=[]
    for name,frame in named_frames:
        by_norm={_norm(c):c for c in frame.columns}
        part=frame[[by_norm[_norm(c)] for c in ordered]].copy()
        part.columns=ordered
        part['_source_file']=name
        prepared.append(part)
    return pd.concat(prepared,ignore_index=True,sort=False),reports
