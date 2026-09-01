from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from src.agents.credit_agent import CreditRiskAgent
from src.agents.forecast_agent import CashflowForecastAgent
from src.config import RANDOM_STATE

def train_credit(df,model_type='boosted',test_size=.2,review_threshold=.5,high_risk_threshold=.6):
    train,test=train_test_split(df,test_size=test_size,stratify=df['default_next_month'],random_state=RANDOM_STATE)
    model=CreditRiskAgent(model_type,review_threshold,high_risk_threshold).fit(train); metrics=model.evaluate(test)
    metrics.update({'split':'stratified random holdout','train_rows':len(train),'test_rows':len(test)}); return model,metrics

def train_forecast(df,model_type='boosted',test_size=.2):
    featured=CashflowForecastAgent(model_type).create_features(df); dates=np.array(sorted(featured['date'].dropna().unique()))
    if len(dates)<10: raise ValueError('Forecast training requires at least 10 distinct dates.')
    cut=dates[max(1,int(len(dates)*(1-test_size)))]; train=featured[featured.date<cut].copy(); test=featured[featured.date>=cut].copy()
    if train.empty or test.empty: raise ValueError('Chronological split produced an empty partition.')
    model=CashflowForecastAgent(model_type).fit(train); metrics=model.evaluate_featured(test)
    metrics.update({'split':'chronological holdout','cutoff_date':str(pd.Timestamp(cut).date()),'train_rows':len(train),'test_rows':len(test)}); return model,metrics
