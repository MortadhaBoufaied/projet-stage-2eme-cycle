from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
import joblib
from src.config import ARTIFACTS_DIR

def safe_company_id(value):
    cleaned=re.sub(r'[^A-Za-z0-9_-]+','_',value.strip())
    if not cleaned: raise ValueError('Company ID cannot be empty.')
    return cleaned[:80]
class ModelRegistry:
    def __init__(self,root=ARTIFACTS_DIR): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def company_dir(self,company_id,create=False):
        p=self.root/safe_company_id(company_id)
        if create: p.mkdir(parents=True,exist_ok=True)
        return p
    def save(self,company_id,task,model,metadata):
        d=self.company_dir(company_id,True)/task; d.mkdir(parents=True,exist_ok=True); stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        model_path=d/f'model_{stamp}.joblib'; joblib.dump(model,model_path)
        payload={**metadata,'company_id':safe_company_id(company_id),'task':task,'model_file':model_path.name,'version':stamp,'saved_at_utc':stamp}
        (d/f'metadata_{stamp}.json').write_text(json.dumps(payload,indent=2),encoding='utf-8'); (d/'latest.json').write_text(json.dumps(payload,indent=2),encoding='utf-8'); return model_path
    def load_latest(self,company_id,task):
        d=self.company_dir(company_id)/task; p=d/'latest.json'
        if not p.exists(): raise FileNotFoundError(f'No saved {task} model for {company_id}.')
        meta=json.loads(p.read_text(encoding='utf-8')); return joblib.load(d/meta['model_file']),meta
    def versions(self,company_id,task):
        d=self.company_dir(company_id)/task
        if not d.exists(): return []
        return sorted([json.loads(p.read_text(encoding='utf-8')) for p in d.glob('metadata_*.json')],key=lambda x:x['saved_at_utc'],reverse=True)
    def activate(self,company_id,task,version):
        d=self.company_dir(company_id)/task; p=d/f'metadata_{version}.json'
        if not p.exists(): raise FileNotFoundError('Model version not found.')
        (d/'latest.json').write_text(p.read_text(encoding='utf-8'),encoding='utf-8')
    def list_companies(self): return sorted([p.name for p in self.root.iterdir() if p.is_dir()])
