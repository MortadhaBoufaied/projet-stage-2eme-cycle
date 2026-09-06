from pathlib import Path
from datetime import datetime,timezone
import json,uuid,pandas as pd
from src.config import ARTIFACTS
def safe(s): return ''.join(c for c in s if c.isalnum() or c in '_-')[:64]
class Workspace:
    def __init__(self,company): self.root=ARTIFACTS/'workspaces'/safe(company);self.root.mkdir(parents=True,exist_ok=True)
    def save(self,task,source,result,meta):
        aid='ana_'+uuid.uuid4().hex[:12];d=self.root/aid;d.mkdir();source.to_csv(d/'source.csv',index=False);result.to_csv(d/'result.csv',index=False); meta=meta|{'analysis_id':aid,'task':task,'date':datetime.now(timezone.utc).isoformat(),'records':len(source)};(d/'metadata.json').write_text(json.dumps(meta,indent=2,default=str));return aid
    def history(self):
        return sorted([json.loads((p/'metadata.json').read_text()) for p in self.root.iterdir() if (p/'metadata.json').exists()],key=lambda x:x['date'],reverse=True)
