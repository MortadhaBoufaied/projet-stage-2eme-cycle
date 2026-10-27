from __future__ import annotations
import re,pandas as pd
from src.services.schema import suggest_mapping
SENSITIVE=re.compile(r"(name|email|phone|address|ssn|national|passport|iban|account)",re.I)
def safe_sample(df,rows=5):
 d=df.head(rows).copy()
 for c in d.columns:d[c]="[MASKED]" if SENSITIVE.search(str(c)) else d[c].map(lambda v:None if pd.isna(v) else str(v)[:80])
 return d.to_dict("records")
def hybrid_suggest_mapping(df,required,slm_mapper=None):
 required=list(required);mapping=suggest_mapping(df.columns,required);missing=[x for x in required if not mapping.get(x)];report={"obvious_mapped":len(required)-len(missing),"slm_mapped":0,"unresolved":missing}
 if missing and slm_mapper:
  unused=[str(c) for c in df.columns if c not in set(mapping.values())];suggested=slm_mapper(missing,unused,safe_sample(df)) or {};used={v for v in mapping.values() if v}
  for field in missing:
   source=suggested.get(field)
   if source in unused and source not in used:mapping[field]=source;used.add(source);report["slm_mapped"]+=1
 report["unresolved"]=[x for x in required if not mapping.get(x)];return mapping,report
