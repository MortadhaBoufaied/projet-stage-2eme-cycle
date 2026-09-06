from __future__ import annotations
import numpy as np,pandas as pd
class PaymentRiskAssessmentAgent:
 """Orchestrates internal behavior and loan-profile models inside one service."""
 @staticmethod
 def _decision(a,b):
  levels={'LOW_RISK':0,'MEDIUM_RISK':1,'HIGH_RISK':2};values=[x for x in [a,b] if x]
  if not values:return 'UNAVAILABLE','No compatible model input was supplied.'
  top=max(levels[x] for x in values)
  if top==2:return 'MANUAL_REVIEW','At least one internal model reports high risk.'
  if len(values)==2 and all(x=='MEDIUM_RISK' for x in values):return 'MANUAL_REVIEW','Both internal models report medium risk.'
  if top==1:return 'REVIEW_RECOMMENDED','At least one internal model reports medium risk.'
  return 'STANDARD_PROCESS','All available internal models report low risk.'
 def analyze(self,behavior_model=None,behavior_df=None,loan_model=None,loan_df=None,id_column='client_id'):
  frames=[]
  if behavior_model is not None and behavior_df is not None:
   p,t=behavior_model.predict_risk(behavior_df);ids=behavior_df[id_column].astype(str) if id_column in behavior_df else behavior_df.index.astype(str);frames.append(pd.DataFrame({'client_id':ids,'behavior_probability':p,'behavior_tier':t}))
  if loan_model is not None and loan_df is not None:
   p,t=loan_model.predict_risk(loan_df);key='LoanID' if 'LoanID' in loan_df else id_column;ids=loan_df[key].astype(str) if key in loan_df else loan_df.index.astype(str);frames.append(pd.DataFrame({'client_id':ids,'loan_probability':p,'loan_tier':t}))
  if not frames:return pd.DataFrame()
  result=frames[0]
  for f in frames[1:]:result=result.merge(f,on='client_id',how='outer')
  decisions=[self._decision(r.get('behavior_tier') if pd.notna(r.get('behavior_tier')) else None,r.get('loan_tier') if pd.notna(r.get('loan_tier')) else None) for _,r in result.iterrows()]
  result['final_status']=[x[0] for x in decisions];result['decision_reason']=[x[1] for x in decisions];result['models_used']=result.apply(lambda r:' + '.join(x for x,v in [('Payment behavior',r.get('behavior_probability')),('Loan profile',r.get('loan_probability'))] if pd.notna(v)),axis=1)
  return result
