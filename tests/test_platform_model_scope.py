import json
from src.services.model_registry import ModelRegistry,PLATFORM_MODEL_OWNER

class Dummy:pass

def test_platform_model_is_available_to_every_company(tmp_path):
 r=ModelRegistry(tmp_path)
 r.save_platform('forecast',Dummy(),{'mapping':{'date':'Date'}})
 first,meta1=r.load_platform('forecast')
 second,meta2=r.load_platform('forecast')
 assert isinstance(first,Dummy) and isinstance(second,Dummy)
 assert meta1['scope']=='platform' and meta1['available_to_all_companies'] is True
 assert (tmp_path/PLATFORM_MODEL_OWNER/'forecast'/'active.json').is_file()

def test_old_admin_trained_model_is_discovered_as_legacy_platform_model(tmp_path):
 r=ModelRegistry(tmp_path)
 r.save('admin_selected_company','credit',Dummy(),{'mapping':{}},True)
 model,meta=r.load_platform('credit')
 assert isinstance(model,Dummy) and meta['task']=='credit'
