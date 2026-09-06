import pandas as pd,numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor,HistGradientBoostingClassifier
from xgboost import XGBClassifier,XGBRegressor
from .metrics import classification,regression
from src.services.validation import normalize
from src.services.schemas import TARGETS

def _prep(X):
 cats=list(X.select_dtypes(exclude=np.number).columns);nums=[c for c in X if c not in cats]
 return ColumnTransformer([('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore'))]),cats),('num',SimpleImputer(strategy='median'),nums)])
def train_credit(df,algo='xgboost'):
 d=normalize(df);target=TARGETS['credit'];X=d.drop(columns=[target,'client_id'],errors='ignore');y=pd.to_numeric(d[target]).astype(int)
 Xtr,Xtmp,ytr,ytmp=train_test_split(X,y,test_size=.3,stratify=y,random_state=42);Xv,Xte,yv,yte=train_test_split(Xtmp,ytmp,test_size=.5,stratify=ytmp,random_state=42)
 est={'logistic':LogisticRegression(max_iter=1500,class_weight='balanced'),'random_forest':RandomForestClassifier(n_estimators=250,class_weight='balanced',random_state=42,n_jobs=-1),'xgboost':XGBClassifier(n_estimators=300,max_depth=4,learning_rate=.05,subsample=.85,colsample_bytree=.85,eval_metric='aucpr',random_state=42,n_jobs=-1)}[algo]
 m=Pipeline([('pre',_prep(Xtr)),('model',est)]).fit(Xtr,ytr)
 return m,{'train':classification(ytr,m.predict_proba(Xtr)[:,1]),'validation':classification(yv,m.predict_proba(Xv)[:,1]),'test':classification(yte,m.predict_proba(Xte)[:,1]),'split':{'method':'stratified','train':len(Xtr),'validation':len(Xv),'test':len(Xte)},'features':list(X.columns),'target':target,'algorithm':algo}
def train_forecast(df,algo='xgboost'):
 d=normalize(df);d['date']=pd.to_datetime(d.date);d=d.sort_values('date');target=TARGETS['forecast'] if TARGETS['forecast'] in d else 'units_sold';feature_cols=['store_id','product_id','category','region','inventory_level','units_ordered','price']
 for c in feature_cols:
  if c not in d:d[c]=np.nan
 X=d[feature_cols];y=pd.to_numeric(d[target]);a=int(len(d)*.7);b=int(len(d)*.85);parts=(slice(0,a),slice(a,b),slice(b,None))
 est={'ridge':Ridge(),'random_forest':RandomForestRegressor(n_estimators=200,random_state=42,n_jobs=-1),'xgboost':XGBRegressor(n_estimators=300,max_depth=5,learning_rate=.05,objective='reg:squarederror',random_state=42,n_jobs=-1)}[algo]
 m=Pipeline([('pre',_prep(X.iloc[parts[0]])),('model',est)]).fit(X.iloc[parts[0]],y.iloc[parts[0]])
 return m,{'train':regression(y.iloc[parts[0]],m.predict(X.iloc[parts[0]])),'validation':regression(y.iloc[parts[1]],m.predict(X.iloc[parts[1]])),'test':regression(y.iloc[parts[2]],m.predict(X.iloc[parts[2]])),'split':{'method':'chronological','train':a,'validation':b-a,'test':len(d)-b},'features':list(X.columns),'target':target,'algorithm':algo}
