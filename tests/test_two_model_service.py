import pandas as pd
from src.agents.payment_risk_agent import PaymentRiskAssessmentAgent
class M:
 def __init__(self,p,t):self.p=p;self.t=t
 def predict_risk(self,d):return [self.p]*len(d),[self.t]*len(d)
def test_one_service_combines_internal_model_decisions():
 d=pd.DataFrame({'client_id':['A']});l=pd.DataFrame({'LoanID':['A']});r=PaymentRiskAssessmentAgent().analyze(M(.7,'HIGH_RISK'),d,M(.2,'LOW_RISK'),l)
 assert r.iloc[0].final_status=='MANUAL_REVIEW' and ' + ' in r.iloc[0].models_used
