from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from src.config import ARTIFACTS_DIR
DEFAULT_LIMIT_BYTES=500*1024*1024
CACHE_DIR=Path(ARTIFACTS_DIR)/"managed_training_files"

def uploaded_size(file):
 if getattr(file,"size",None) is not None:return int(file.size)
 pos=file.tell();file.seek(0,2);size=file.tell();file.seek(pos);return int(size)

def upload_summary(files):
 files=list(files or [])
 return {"files":len(files),"source_bytes":sum(uploaded_size(f) for f in files),"names":[getattr(f,"name","uploaded.csv") for f in files]}

def cache_key(files,target_bytes,seed=42):
 signature=[(getattr(f,"name","uploaded.csv"),uploaded_size(f)) for f in files]
 raw=json.dumps({"files":signature,"target":int(target_bytes),"seed":seed},sort_keys=True).encode()
 return hashlib.sha256(raw).hexdigest()[:20]

def managed_paths(files,target_bytes,seed=42):
 key=cache_key(files,target_bytes,seed);CACHE_DIR.mkdir(parents=True,exist_ok=True)
 return CACHE_DIR/f"reduced_{key}.csv",CACHE_DIR/f"reduced_{key}.json"

def _write_under_limit(df,path,target_bytes,seed):
 path.parent.mkdir(parents=True,exist_ok=True);df.to_csv(path,index=False)
 actual=path.stat().st_size
 while actual>target_bytes and len(df)>1:
  fraction=min(.995,target_bytes*.985/actual)
  df=df.sample(frac=fraction,random_state=seed).reset_index(drop=True)
  df.to_csv(path,index=False);actual=path.stat().st_size
 return df,actual

def prepare_csv_uploads(files,target_bytes,seed=42,progress=None,chunksize=100_000):
 files=list(files or [])
 if not files:raise ValueError("Upload at least one CSV file.")
 if not 10*1024*1024<=int(target_bytes)<=500*1024*1024:raise ValueError("Reduced size must be between 10 MB and 500 MB.")
 output,meta_path=managed_paths(files,target_bytes,seed)
 if output.exists() and meta_path.exists():
  report=json.loads(meta_path.read_text(encoding="utf-8"));report["cached"]=True
  if progress:progress(92,"Loading the previously prepared reduced file...")
  return pd.read_csv(output),report,output
 total=sum(uploaded_size(f) for f in files);ratio=min(1.0,target_bytes*.94/max(total,1));rng=np.random.default_rng(seed);parts=[];rows_read=0
 for i,f in enumerate(files,1):
  f.seek(0)
  try:reader=pd.read_csv(f,sep=None,engine="python",chunksize=chunksize)
  except Exception:f.seek(0);reader=pd.read_csv(f,chunksize=chunksize)
  for chunk in reader:
   rows_read+=len(chunk)
   if ratio<1:chunk=chunk.loc[rng.random(len(chunk))<ratio]
   if not chunk.empty:parts.append(chunk)
  if progress:progress(min(70,10+int(60*i/len(files))),f"Read and sampled {i} of {len(files)} file(s)...")
 if not parts:raise ValueError("No rows remained after random reduction.")
 df=pd.concat(parts,ignore_index=True,sort=False)
 if progress:progress(78,"Writing the reduced CSV and checking its actual size...")
 df,actual=_write_under_limit(df,output,int(target_bytes),seed)
 report={"source_files":len(files),"source_bytes":total,"target_bytes":int(target_bytes),"rows_read":rows_read,"rows_kept":len(df),"rows_removed":rows_read-len(df),"actual_output_bytes":actual,"reduced":rows_read>len(df),"seed":seed,"cached":False}
 meta_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
 return df,report,output
