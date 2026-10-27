from __future__ import annotations
from dataclasses import asdict, is_dataclass
import hashlib, json, re
import pandas as pd


def norm(v): return re.sub(r'[^a-z0-9]+','',str(v).strip().lower())

def schema_payload(schema, source_columns=None):
    cols=[]
    for c in schema.columns:
        cols.append(asdict(c) if is_dataclass(c) else dict(c))
    payload={
        'columns':cols,'source_columns':list(source_columns) if source_columns is not None else [c['name'] for c in cols],
        'target':schema.suggested_target,'features':list(schema.suggested_features),
        'ids':list(schema.suggested_ids),'task_type':schema.task_type,
    }
    payload['prediction_columns']=[c for c in payload['source_columns'] if c != payload['target'] and c in set(payload['features']+payload['ids'])]
    raw=json.dumps({k:payload[k] for k in ('columns','target','features','ids','task_type')},sort_keys=True,default=str)
    payload['fingerprint']=hashlib.sha256(raw.encode()).hexdigest()
    return payload

def contract_from_metadata(metadata):
    meta=metadata or {}; contract=dict(meta.get('schema_contract') or {})
    contract.setdefault('features',list(meta.get('features') or []))
    contract.setdefault('target',meta.get('target'))
    contract.setdefault('ids',list(meta.get('id_columns') or []))
    contract.setdefault('prediction_columns',list(contract.get('features') or []))
    return contract

def prediction_template(metadata, include_example=False):
    contract=contract_from_metadata(metadata); columns=contract.get('prediction_columns') or contract.get('features') or []
    if not include_example:return pd.DataFrame(columns=columns)
    info={c.get('name'):c for c in contract.get('columns',[])}; row={}
    for name in columns:
        item=info.get(name,{})
        samples=item.get('sample_values') or []
        row[name]=samples[0] if samples else ''
    return pd.DataFrame([row],columns=columns)

def documentation(metadata):
    contract=contract_from_metadata(metadata); rows=[]
    for c in contract.get('columns',[]):
        if c.get('name') in set(contract.get('prediction_columns',[])):
            rows.append({'column':c.get('name'),'type':c.get('dtype','unknown'),'role':'identifier' if c.get('name') in contract.get('ids',[]) else 'feature','nullable':c.get('nullable',True),'example':(c.get('sample_values') or [''])[0]})
    return pd.DataFrame(rows)

def align_upload(frame, metadata):
    contract=contract_from_metadata(metadata); required=list(contract.get('features') or [])
    ids=list(contract.get('ids') or []); by_norm={norm(c):c for c in frame.columns}; rename={};missing=[]
    for name in required+ids:
        if name in frame:continue
        src=by_norm.get(norm(name))
        if src is None:
            if name in required:missing.append(name)
        else:rename[src]=name
    aligned=frame.rename(columns=rename).copy()
    return aligned,required,missing

def validate_upload(frame, metadata):
    aligned,features,missing=align_upload(frame,metadata);issues=[]
    if aligned.empty:issues.append({'level':'error','message':'The uploaded dataset is empty.'})
    if missing:issues.append({'level':'error','message':'The file does not match the active model structure. Missing: '+', '.join(missing)})
    extra=[c for c in aligned if c not in set(features+contract_from_metadata(metadata).get('ids',[]))]
    if extra:issues.append({'level':'info','message':'Extra columns are retained for traceability but not used by the model: '+', '.join(extra)})
    return aligned,{'valid':not any(i['level']=='error' for i in issues),'rows':len(aligned),'columns':len(aligned.columns),'duplicates':int(aligned.duplicated().sum()),'missing_cells':int(aligned.isna().sum().sum()),'issues':issues}
