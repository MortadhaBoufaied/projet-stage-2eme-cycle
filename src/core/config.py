from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'; ARTIFACTS=ROOT/'artifacts'; MODELS=ARTIFACTS/'models'; ANALYSES=ARTIFACTS/'analyses'
for p in (DATA,ARTIFACTS,MODELS,ANALYSES): p.mkdir(parents=True,exist_ok=True)
def load_env():
 p=ROOT/'.env'
 if p.exists():
  for line in p.read_text(encoding='utf-8').splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
load_env()
