from src.services.model_registry import ModelRegistry
class Dummy: pass
def test_forget_training_removes_all_saved_versions(tmp_path):
 r=ModelRegistry(tmp_path);item=r.save_candidate("company","credit",Dummy(),{});r.promote("company","credit",item["version"]);assert r.has_training("company","credit");assert r.forget_training("company","credit")==1;assert not r.has_training("company","credit")
