from __future__ import annotations
import json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
import joblib
from src.config import ARTIFACTS_DIR

def safe_company_id(value):
    cleaned=re.sub(r'[^A-Za-z0-9_-]+','_',str(value or '').strip())
    if not cleaned:raise ValueError('No active company workspace is selected.')
    return cleaned[:80]


def normalize_model_metadata(item,task=None):
    item=dict(item or {})
    model_file=item.get('model_file','')
    version=item.get('version') or (Path(model_file).stem.replace('model_','',1) if model_file else 'legacy')
    created=item.get('created_at_utc') or item.get('saved_at_utc') or datetime.now(timezone.utc).isoformat()
    item.update(version=version,status=item.get('status','ARCHIVED'),created_at_utc=created,task=item.get('task',task))
    return item

class ModelRegistry:
    STATUSES={'CANDIDATE','CHALLENGER','CHAMPION','ARCHIVED','REJECTED'}
    def __init__(self,root=ARTIFACTS_DIR):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def company_dir(self,company_id,create=False):
        path=self.root/safe_company_id(company_id)
        if create:path.mkdir(parents=True,exist_ok=True)
        return path
    def _task_dir(self,company_id,task,create=False):
        if task not in {'credit','forecast'}:raise ValueError('Unsupported model task.')
        path=self.company_dir(company_id,create)/task
        if create:path.mkdir(parents=True,exist_ok=True)
        return path
    @staticmethod
    def _write(path,payload):
        temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8');temp.replace(path)
    def save_candidate(self,company_id,task,model,metadata,status='CANDIDATE'):
        if status not in self.STATUSES-{'CHAMPION'}:raise ValueError('Invalid candidate status.')
        directory=self._task_dir(company_id,task,True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        model_path=directory/f'model_{stamp}.joblib';joblib.dump(model,model_path)
        payload={**metadata,'company_id':safe_company_id(company_id),'task':task,'model_file':model_path.name,'version':stamp,'status':status,'created_at_utc':datetime.now(timezone.utc).isoformat(),'activated_at_utc':None,'archived_at_utc':None,'deleted_at_utc':None}
        self._write(directory/f'metadata_{stamp}.json',payload);return payload
    def save_as_champion(self,company_id,task,model,metadata,actor='administrator'):
        candidate=self.save_candidate(company_id,task,model,metadata,'CANDIDATE')
        return self.promote(company_id,task,candidate['version'],actor)
    def save(self,company_id,task,model,metadata,activate=True):
        candidate=self.save_candidate(company_id,task,model,metadata)
        if activate:self.promote(company_id,task,candidate['version'])
        return self._task_dir(company_id,task)/candidate['model_file']
    def _metadata(self,company_id,task,version):
        path=self._task_dir(company_id,task)/f'metadata_{version}.json'
        if not path.exists():raise FileNotFoundError('Model version not found.')
        return path,json.loads(path.read_text(encoding='utf-8'))
    def active_metadata(self,company_id,task):
        pointer=self._task_dir(company_id,task)/'active.json'
        if not pointer.exists():raise FileNotFoundError(f'No active {task} model for {company_id}.')
        meta=normalize_model_metadata(json.loads(pointer.read_text(encoding='utf-8')),task)
        if meta.get('task') != task:
            raise FileNotFoundError(f'No active {task} model for {company_id}.')
        model_path=self._task_dir(company_id,task)/meta.get('model_file','')
        if not model_path.is_file():
            raise FileNotFoundError(f'Active {task} model file is missing for {company_id}.')
        return meta
    def load_latest(self,company_id,task):
        meta=self.active_metadata(company_id,task);directory=self._task_dir(company_id,task)
        return joblib.load(directory/meta['model_file']),meta
    def load_version(self,company_id,task,version):
        _,meta=self._metadata(company_id,task,version)
        return joblib.load(self._task_dir(company_id,task)/meta['model_file']),meta
    def promote(self,company_id,task,version,actor='administrator'):
        directory=self._task_dir(company_id,task);path,new=self._metadata(company_id,task,version);now=datetime.now(timezone.utc).isoformat()
        try:
            current=self.active_metadata(company_id,task)
            if current['version']!=version:
                old_path,old=self._metadata(company_id,task,current['version']);old.update(status='ARCHIVED',archived_at_utc=now);self._write(old_path,old)
        except FileNotFoundError:pass
        new.update(status='CHAMPION',activated_at_utc=now,activated_by=actor,archived_at_utc=None);self._write(path,new);self._write(directory/'active.json',new);return new
    def reject(self,company_id,task,version):
        path,meta=self._metadata(company_id,task,version)
        if meta.get('status')=='CHAMPION':raise ValueError('The active champion cannot be rejected.')
        meta['status']='REJECTED';self._write(path,meta)
    def archive(self,company_id,task,version):
        path,meta=self._metadata(company_id,task,version)
        if meta.get('status')=='CHAMPION':raise ValueError('Activate another version before archiving the champion.')
        meta.update(status='ARCHIVED',archived_at_utc=datetime.now(timezone.utc).isoformat());self._write(path,meta)
    def delete(self,company_id,task,version):
        path,meta=self._metadata(company_id,task,version)
        if meta.get('status')=='CHAMPION':raise ValueError('The active champion cannot be deleted.')
        model_path=self._task_dir(company_id,task)/meta['model_file']
        if model_path.exists():model_path.unlink()
        path.unlink();return True
    def versions(self,company_id,task):
        directory=self._task_dir(company_id,task)
        if not directory.exists():return []
        items=[]
        for path in directory.glob('metadata_*.json'):
            item=normalize_model_metadata(json.loads(path.read_text(encoding='utf-8')),task)
            # A task directory may contain stale/copied metadata from an older build.
            # Never let a payment model mark cashflow as trained, or vice versa.
            if item.get('task') == task:
                items.append(item)
        return sorted(items,key=lambda item:item.get('created_at_utc',item.get('saved_at_utc','')),reverse=True)
    def activate(self,company_id,task,version):return self.promote(company_id,task,version)
    def has_training(self,company_id,task):return bool(self.versions(company_id,task))
    def has_active_training(self,company_id,task):
        try:
            self.active_metadata(company_id,task)
        except FileNotFoundError:
            return False
        return True
    def forget_training(self,company_id,task):
        directory=self._task_dir(company_id,task)
        if not directory.exists():return 0
        count=len(list(directory.glob('metadata_*.json')));shutil.rmtree(directory);return count
    def list_companies(self):return sorted(path.name for path in self.root.iterdir() if path.is_dir())
