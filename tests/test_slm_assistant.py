from src.services import slm_assistant as sa

def test_service_prompts_and_safe_fallback(monkeypatch):
 monkeypatch.setattr(sa,'MODEL_PATH',sa.MODEL_DIR/'missing.gguf')
 payment=sa.analyze('payment',{'high_risk':2,'medium_risk':3})
 forecast=sa.analyze('forecast',{'anomalies':1,'stockout_risks':0})
 lending=sa.analyze('lending',{'high_risk':0,'medium_risk':2})
 assert payment['decision_status']=='MANUAL_REVIEW'
 assert forecast['decision_status']=='INVESTIGATE_VARIANCE'
 assert lending['decision_status']=='REVIEW_RECOMMENDED'
 assert all(x['generated_by']=='deterministic_fallback' for x in [payment,forecast,lending])

def test_model_limit_is_two_gb():
 assert sa.MAX_MODEL_BYTES==2_000_000_000
