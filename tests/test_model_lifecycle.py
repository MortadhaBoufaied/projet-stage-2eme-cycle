from pathlib import Path
import tempfile
from src.services.model_registry import ModelRegistry
class Dummy:pass
def test_candidate_does_not_replace_champion_and_rollback_works():
    with tempfile.TemporaryDirectory() as td:
        registry=ModelRegistry(Path(td));first=registry.save_candidate('company','credit',Dummy(),{'metrics':{'score':1}});registry.promote('company','credit',first['version'])
        second=registry.save_candidate('company','credit',Dummy(),{'metrics':{'score':2}},'CHALLENGER')
        assert registry.active_metadata('company','credit')['version']==first['version']
        registry.promote('company','credit',second['version']);assert registry.active_metadata('company','credit')['version']==second['version']
        registry.promote('company','credit',first['version']);assert registry.active_metadata('company','credit')['version']==first['version']
def test_active_model_cannot_be_deleted():
    with tempfile.TemporaryDirectory() as td:
        registry=ModelRegistry(Path(td));item=registry.save_candidate('company','credit',Dummy(),{});registry.promote('company','credit',item['version'])
        try:registry.delete('company','credit',item['version']);assert False
        except ValueError:pass
