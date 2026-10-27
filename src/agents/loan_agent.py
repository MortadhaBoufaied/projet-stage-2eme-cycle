from __future__ import annotations
import numpy as np,pandas as pd
from xgboost import XGBClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score,average_precision_score,accuracy_score,f1_score,precision_score,recall_score,brier_score_loss,confusion_matrix
from src.services.loan_schema import LOAN_NUMERIC,LOAN_CATEGORICAL,LOAN_TARGET
from src.config import RANDOM_STATE
class LoanDefaultAgent:
 def __init__(self,review_threshold=.25,high_risk_threshold=.5):self.review_threshold=review_threshold;self.high_risk_threshold=high_risk_threshold;self.model=None
 def fit(self,df):
  y=pd.to_numeric(df[LOAN_TARGET]).astype(int);weight=max((y==0).sum(),1)/max((y==1).sum(),1)
  pre=ColumnTransformer([('num',SimpleImputer(strategy='median'),LOAN_NUMERIC),('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore'))]),LOAN_CATEGORICAL)])
  xgb=XGBClassifier(n_estimators=500,max_depth=5,learning_rate=.04,subsample=.85,colsample_bytree=.85,reg_lambda=2,objective='binary:logistic',eval_metric='aucpr',scale_pos_weight=weight,tree_method='hist',random_state=RANDOM_STATE,n_jobs=-1)
  self.model=Pipeline([('pre',pre),('model',xgb)]).fit(df,y);return self
 def predict_proba(self,df):return self.model.predict_proba(df)[:,1]
 def predict_risk(self,df):
  p=self.predict_proba(df);tiers=np.where(p<self.review_threshold,'LOW_RISK',np.where(p<self.high_risk_threshold,'MEDIUM_RISK','HIGH_RISK'));return p,tiers.tolist()
 def evaluate(self,df):
  y=pd.to_numeric(df[LOAN_TARGET]).astype(int).to_numpy();p=self.predict_proba(df);pred=(p>=self.review_threshold).astype(int);cm=confusion_matrix(y,pred,labels=[0,1])
  return {'ROC_AUC':round(float(roc_auc_score(y,p)),4),'PR_AUC':round(float(average_precision_score(y,p)),4),'Accuracy':round(float(accuracy_score(y,pred)),4),'F1_Score':round(float(f1_score(y,pred)),4),'Precision':round(float(precision_score(y,pred)),4),'Recall':round(float(recall_score(y,pred)),4),'Brier_Score':round(float(brier_score_loss(y,p)),4),'Confusion_Matrix':cm.tolist(),'n_test':len(y)}
