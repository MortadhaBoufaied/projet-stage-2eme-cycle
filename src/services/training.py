from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from src.agents.credit_agent import CreditRiskAgent
from src.agents.forecast_agent import CashflowForecastAgent
from src.services.augmentation import augment_credit_training_data
from src.config import RANDOM_STATE

def fixed_credit_split(df,test_size=.2):
    return train_test_split(df,test_size=test_size,stratify=df['default_next_month'],random_state=RANDOM_STATE)

def train_credit(df,model_type='xgboost',test_size=.2,review_threshold=.5,high_risk_threshold=.6,augmentation=None):
    train,test=fixed_credit_split(df,test_size)
    augmentation_meta={"synthetic_rows":0,"original_rows":len(train),"augmented_rows":len(train)}
    fit_data=train
    if augmentation:
        fit_data,augmentation_meta=augment_credit_training_data(train,target_ratio=augmentation.get("target_ratio",.75),jitter=augmentation.get("jitter",.025))
    model=CreditRiskAgent(model_type,review_threshold,high_risk_threshold).fit(fit_data);metrics=model.evaluate(test)
    metrics.update({'split':'fixed stratified holdout','train_rows':len(train),'fit_rows':len(fit_data),'test_rows':len(test),'model_type':model_type,'augmentation':augmentation_meta})
    return model,metrics

def compare_credit_augmentation(df,model_type='xgboost',test_size=.2,review_threshold=.5,high_risk_threshold=.6,target_ratio=.75,jitter=.025):
    train,test=fixed_credit_split(df,test_size)
    base=CreditRiskAgent(model_type,review_threshold,high_risk_threshold).fit(train);base_metrics=base.evaluate(test)
    enlarged,meta=augment_credit_training_data(train,target_ratio,jitter)
    augmented=CreditRiskAgent(model_type,review_threshold,high_risk_threshold).fit(enlarged);aug_metrics=augmented.evaluate(test)
    keys=["ROC_AUC","PR_AUC","F1_Score","Precision","Recall","Brier_Score"]
    comparison=[{"metric":k,"before":base_metrics[k],"after":aug_metrics[k],"change":round(aug_metrics[k]-base_metrics[k],4)} for k in keys]
    # PR AUC is primary for imbalance, ROC AUC secondary. Lower Brier is better.
    score=(aug_metrics["PR_AUC"]-base_metrics["PR_AUC"])*2+(aug_metrics["ROC_AUC"]-base_metrics["ROC_AUC"])+(base_metrics["Brier_Score"]-aug_metrics["Brier_Score"])*.5
    accepted=score>0 and aug_metrics["Recall"]>=base_metrics["Recall"]-.02
    return {"baseline_model":base,"augmented_model":augmented,"baseline_metrics":base_metrics,"augmented_metrics":aug_metrics,"comparison":comparison,"augmentation":meta,"recommended":"augmented" if accepted else "baseline","decision_score":round(float(score),5)}

def train_forecast(df,model_type='boosted',test_size=.2):
    featured=CashflowForecastAgent(model_type).create_features(df);dates=np.array(sorted(featured['date'].dropna().unique()))
    if len(dates)<10:raise ValueError('Forecast training requires at least 10 distinct dates.')
    cut=dates[max(1,int(len(dates)*(1-test_size)))];train=featured[featured.date<cut].copy();test=featured[featured.date>=cut].copy()
    if train.empty or test.empty:raise ValueError('Chronological split produced an empty partition.')
    model=CashflowForecastAgent(model_type).fit(train);metrics=model.evaluate_featured(test);metrics.update({'split':'chronological holdout','cutoff_date':str(pd.Timestamp(cut).date()),'train_rows':len(train),'test_rows':len(test)});return model,metrics
