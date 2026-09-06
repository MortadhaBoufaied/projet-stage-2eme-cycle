import numpy as np,pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor,HistGradientBoostingClassifier
from xgboost import XGBClassifier,XGBRegressor
from .schemas import CREDIT_FIELDS,CREDIT_TARGET,FORECAST_FIELDS
from .metrics import classification,regression
RS=42
def _credit_est(name):
    if name=='Logistic Regression': return Pipeline([('imp',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(max_iter=2000,class_weight='balanced',random_state=RS))])
    if name=='Random Forest': return Pipeline([('imp',SimpleImputer(strategy='median')),('model',RandomForestClassifier(n_estimators=250,class_weight='balanced',n_jobs=-1,random_state=RS))])
    return Pipeline([('imp',SimpleImputer(strategy='median')),('model',XGBClassifier(n_estimators=350,max_depth=4,learning_rate=.04,subsample=.85,colsample_bytree=.85,eval_metric='aucpr',n_jobs=-1,random_state=RS))])
def train_credit(df,algorithms):
    feats=[f.name for f in CREDIT_FIELDS if f.used]; X=df[feats].apply(pd.to_numeric,errors='coerce'); y=pd.to_numeric(df[CREDIT_TARGET.name]).astype(int)
    Xtr,Xtmp,ytr,ytmp=train_test_split(X,y,test_size=.3,stratify=y,random_state=RS); Xv,Xte,yv,yte=train_test_split(Xtmp,ytmp,test_size=.5,stratify=ytmp,random_state=RS)
    runs=[]
    for name in algorithms:
        m=_credit_est(name).fit(Xtr,ytr); runs.append({'algorithm':name,'model':m,'validation':classification(yv,m.predict_proba(Xv)[:,1]),'test':classification(yte,m.predict_proba(Xte)[:,1]),'features':feats,'split':{'train':len(Xtr),'validation':len(Xv),'test':len(Xte),'method':'stratified'}})
    best=max(runs,key=lambda r:(r['validation']['PR-AUC'] or -1,r['validation']['F1'])); return runs,best
def _forecast_model(name,cat,num):
    pre=ColumnTransformer([('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),cat),('num',SimpleImputer(strategy='median'),num)])
    model=Ridge(1.0) if name=='Ridge' else (RandomForestRegressor(n_estimators=200,n_jobs=-1,random_state=RS) if name=='Random Forest' else XGBRegressor(n_estimators=350,max_depth=5,learning_rate=.04,n_jobs=-1,random_state=RS))
    return Pipeline([('pre',pre),('model',model)])
def forecast_features(df):
    d=df.copy();d['date']=pd.to_datetime(d.date);d=d.sort_values(['store_id','product_id','date']);d['dow']=d.date.dt.dayofweek;d['month']=d.date.dt.month
    g=d.groupby(['store_id','product_id'])['units_sold'];
    for lag in (1,7,14): d[f'lag_{lag}']=g.shift(lag)
    return d
def train_forecast(df,algorithms):
    d=forecast_features(df); dates=sorted(d.date.dropna().unique()); a=dates[int(len(dates)*.7)]; b=dates[int(len(dates)*.85)]; tr=d[d.date<a]; va=d[(d.date>=a)&(d.date<b)]; te=d[d.date>=b]
    cat=['store_id','product_id','category','region']; num=['inventory_level','units_ordered','price','dow','month','lag_1','lag_7','lag_14']; num=[c for c in num if c in d]; feats=cat+num; runs=[]
    for name in algorithms:
        m=_forecast_model(name,cat,num).fit(tr[feats],tr.units_sold); runs.append({'algorithm':name,'model':m,'validation':regression(va.units_sold,m.predict(va[feats])),'test':regression(te.units_sold,m.predict(te[feats])),'features':feats,'split':{'train':len(tr),'validation':len(va),'test':len(te),'method':'chronological'}})
    best=min(runs,key=lambda r:r['validation']['WAPE'] if r['validation']['WAPE'] is not None else 1e99); return runs,best
