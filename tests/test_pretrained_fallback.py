import json,tempfile
from pathlib import Path
import joblib
import src.services.model_registry as mr
class Dummy:
 def predict_risk(self,df):return [0.1]*len(df),['LOW_RISK']*len(df)
def test_bundled_fallback_and_company_override(monkeypatch):
 with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as pd:
  pre=Path(pd);(pre/'credit').mkdir();joblib.dump(Dummy(),pre/'credit'/'default.joblib');(pre/'credit'/'active.json').write_text(json.dumps({'model_file':'default.joblib','task':'credit','version':'bundled','status':'CHAMPION'}))
  monkeypatch.setattr(mr,'PRETRAINED_MODELS_DIR',pre);r=mr.ModelRegistry(Path(td));model,meta=r.load_latest('new_company','credit');assert meta['using_default_model'] is True
  assert r.install_defaults_for_company('new_company')==['credit'];_,meta2=r.load_latest('new_company','credit');assert not meta2.get('using_default_model',False)
