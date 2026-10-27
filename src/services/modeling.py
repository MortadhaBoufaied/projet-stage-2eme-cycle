import numpy as np,pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier, ExtraTreesRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor, GradientBoostingClassifier, GradientBoostingRegressor)
from xgboost import XGBClassifier,XGBRegressor
from .schemas import CREDIT_FIELDS,CREDIT_TARGET,FORECAST_FIELDS
from .metrics import classification,regression
import warnings
from src.services.customer_history import HISTORY_FEATURES, enrich_training_history, add_date_features
RS=42
def _credit_est(name):
    # Balanced fast defaults. Every label maps to its real estimator.
    if name == 'Logistic Regression':
        model = LogisticRegression(max_iter=600, class_weight='balanced', solver='liblinear', random_state=RS)
        return Pipeline([('imp', SimpleImputer(strategy='median')), ('scale', StandardScaler()), ('model', model)])
    if name == 'Random Forest':
        model = RandomForestClassifier(n_estimators=140, max_depth=18, min_samples_leaf=2, class_weight='balanced', n_jobs=-1, random_state=RS)
    elif name == 'Extra Trees':
        model = ExtraTreesClassifier(n_estimators=140, max_depth=22, min_samples_leaf=2, class_weight='balanced', n_jobs=-1, random_state=RS)
    elif name == 'Hist Gradient Boosting':
        model = HistGradientBoostingClassifier(max_iter=140, learning_rate=.07, max_depth=7, random_state=RS)
    elif name == 'Gradient Boosting':
        model = GradientBoostingClassifier(n_estimators=120, learning_rate=.06, max_depth=3, random_state=RS)
    elif name == 'XGBoost':
        model = XGBClassifier(n_estimators=180, max_depth=4, learning_rate=.06, subsample=.85, colsample_bytree=.85, tree_method='hist', eval_metric='aucpr', n_jobs=-1, random_state=RS)
    else:
        raise ValueError(f'Unsupported credit algorithm: {name}')
    return Pipeline([('imp', SimpleImputer(strategy='median')), ('model', model)])

def _date(s):
    raw=s.astype("string").str.strip().str.replace(r"\.0$","",regex=True)
    a=pd.to_datetime(raw.where(raw.str.fullmatch(r"\d{8}")),format="%Y%m%d",errors="coerce")
    return a.fillna(pd.to_datetime(raw,errors="coerce"))

def train_credit(df,algorithms,feature_columns=None,target_column=None,column_meanings=None,progress_callback=None):
    column_meanings={str(k):str(v).strip() for k,v in (column_meanings or {}).items() if str(v).strip()}
    d=df.copy(); requested=list(feature_columns or [str(c) for c in d.columns]); target_col=target_column or CREDIT_TARGET.name
    source_columns=[str(c) for c in d.columns]
    prediction_input_columns=[str(c) for c in requested if c in d.columns and c != target_col]
    # Build leakage-safe customer history features. For each invoice, only earlier
    # payments whose clear date was already known at that invoice date are used.
    d = enrich_training_history(d)
    if any(c in d.columns for c in HISTORY_FEATURES):
        requested = list(dict.fromkeys(requested + HISTORY_FEATURES))
    input_contract=[]
    identifier_terms={"cust_number","customer_id","client_id","doc_id","invoice_id","posting_id"}
    outcome_terms={str(target_col).lower(),"is_late","default_next_month","clear_date","clearing_date","payment_date","isopen","is_open"}
    for column in source_columns:
        series=d[column]
        samples=[str(v) for v in series.dropna().head(3).tolist()]
        key=str(column).strip().lower().replace(" ","_")
        if column == target_col or key in outcome_terms:
            role="training outcome / excluded at prediction"
        elif key in identifier_terms or key.endswith("_id"):
            role="identifier / traceability"
        elif column in prediction_input_columns:
            role="prediction input"
        else:
            role="training source / excluded by administrator or governance"
        input_contract.append({"name":str(column),"dtype":str(series.dtype),"required":column in prediction_input_columns,"example":samples[0] if samples else "","examples":samples,"source_order":source_columns.index(str(column)),"role":role,"meaning":column_meanings.get(str(column),""),"used_by_model":column in prediction_input_columns})
    names={str(c).strip().lower().replace(" ","_"):c for c in d.columns}
    due=next((names[x] for x in ("due_in_date","due_date") if x in names),None)
    clear=next((names[x] for x in ("clear_date","clearing_date","payment_date") if x in names),None)
    if due and clear:
        dv,cv=_date(d[due]),_date(d[clear]); known=dv.notna()&cv.notna(); y=(cv[known]>dv[known]).astype(int); d=d.loc[known].copy(); actual_target="is_late"; target_source="derived from clearing date and due date; open invoices excluded"
    else:
        if target_col not in d: raise ValueError(f"Missing target column: {target_col}")
        raw=pd.to_numeric(d[target_col],errors="coerce");known=raw.isin([0,1]);y=raw[known].astype(int);d=d.loc[known].copy();actual_target=target_col;target_source="uploaded binary target"
    if len(y)<100 or y.nunique()!=2 or y.value_counts().min()<20: raise ValueError("Target requires two classes with at least 20 observations each.")
    leakage={"clear_date","clearing_date","payment_date","paid_date","due_in_date","due_date","delay_days","days_late","is_late","isopen","is_open","payment_status","default_next_month","dataset_source",str(target_col).lower()}
    feats=[];removed={}
    for c in requested:
        if c not in d: continue
        n=str(c).strip().lower().replace(" ","_")
        if n in leakage or "date" in n: removed[c]="outcome/date leakage";continue
        if any(x in n for x in ("invoice_id","doc_id","client_id","customer_name","name_customer","cust_number")): removed[c]="identifier";continue
        u=d[c].nunique(dropna=True)
        if u<=1: removed[c]="constant";continue
        if d[c].dtype==object and u>min(500,max(50,int(len(d)*.02))): removed[c]="high-cardinality text";continue
        feats.append(c)
    if not feats: raise ValueError("No safe features remain after leakage checks.")
    X=d[feats].copy(); nums=list(X.select_dtypes(include=np.number).columns);cats=[c for c in feats if c not in nums]
    transformers=[]
    if nums: transformers.append(("num",Pipeline([("imp",SimpleImputer(strategy="median")),("scale",StandardScaler())]),nums))
    if cats: transformers.append(("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore",min_frequency=5,sparse_output=False))]),cats))
    pre=ColumnTransformer(transformers)
    post=names.get("posting_date") or names.get("invoice_date")
    dates=_date(d[post]) if post else None
    if dates is not None and dates.notna().mean()>=.7 and dates.nunique()>=10:
        order=dates.sort_values(kind="stable").index;X=X.loc[order];y=y.loc[order];a=int(len(X)*.7);b=int(len(X)*.85);Xtr,Xv,Xte=X.iloc[:a],X.iloc[a:b],X.iloc[b:];ytr,yv,yte=y.iloc[:a],y.iloc[a:b],y.iloc[b:];method="chronological"
    else:
        Xtr,Xtmp,ytr,ytmp=train_test_split(X,y,test_size=.3,stratify=y,random_state=RS);Xv,Xte,yv,yte=train_test_split(Xtmp,ytmp,test_size=.5,stratify=ytmp,random_state=RS);method="stratified"
    runs=[]
    total_algs = len(algorithms)
    for idx, name in enumerate(algorithms):
        if progress_callback:
            progress_callback(idx, total_algs, name)
        est = _credit_est(name)
        m=Pipeline([("pre",pre),("model",est)]).fit(Xtr,ytr)
        runs.append({"algorithm":name,"model":m,"validation":classification(yv,m.predict_proba(Xv)[:,1]),"test":classification(yte,m.predict_proba(Xte)[:,1]),"features":feats,"raw_features":prediction_input_columns,"prediction_input_columns":prediction_input_columns,"training_source_columns":source_columns,"input_contract":input_contract,"numeric_features":nums,"categorical_features":cats,"target":actual_target,"target_source":target_source,"removed_features":removed,"column_meanings":column_meanings,"split":{"train":len(Xtr),"validation":len(Xv),"test":len(Xte),"method":method}})
    if progress_callback:
        progress_callback(total_algs, total_algs, "Training complete")
    best=max(runs,key=lambda r:(r["validation"].get("PR-AUC") or -1,r["validation"].get("F1") or -1));return runs,best

def _forecast_model(name,cat,num):
    pre=ColumnTransformer([('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=2, max_categories=50, sparse_output=False))]),cat),('num',SimpleImputer(strategy='median'),num)])
    if name=='Ridge': model=Ridge(1.0)
    elif name=='Random Forest': model=RandomForestRegressor(n_estimators=120,max_depth=14,min_samples_leaf=4,n_jobs=-1,random_state=RS)
    elif name=='Extra Trees': model=ExtraTreesRegressor(n_estimators=120,max_depth=16,min_samples_leaf=3,n_jobs=-1,random_state=RS)
    elif name=='Hist Gradient Boosting': model=HistGradientBoostingRegressor(max_iter=140,learning_rate=.07,max_depth=7,l2_regularization=1.0,random_state=RS)
    elif name=='Gradient Boosting': model=GradientBoostingRegressor(n_estimators=120,learning_rate=.06,max_depth=3,random_state=RS)
    elif name=='XGBoost': model=XGBRegressor(n_estimators=180,max_depth=5,learning_rate=.06,subsample=.85,colsample_bytree=.85,n_jobs=-1,random_state=RS)
    else: raise ValueError(f"Unsupported forecasting algorithm: {name}")
    return Pipeline([('pre',pre),('model',model)])
def forecast_features(df):
    d=df.copy();d['date']=pd.to_datetime(d.date);d=d.sort_values(['store_id','product_id','date']);d['dow']=d.date.dt.dayofweek;d['month']=d.date.dt.month
    g=d.groupby(['store_id','product_id'])['units_sold'];
    for lag in (1,7,14): d[f'lag_{lag}']=g.shift(lag)
    return d
def train_forecast(df,algorithms,feature_columns=None,target_column=None,column_meanings=None):
    column_meanings={str(k):str(v).strip() for k,v in (column_meanings or {}).items() if str(v).strip()}
    source=df.copy(); source_columns=[str(c) for c in source.columns]
    target=target_column if target_column is not None else 'units_sold'
    prediction_input_columns=[str(c) for c in (feature_columns or source_columns) if c in source.columns and c != target]
    input_contract=[]
    for column in source_columns:
        series=source[column]; samples=[str(v) for v in series.dropna().head(3).tolist()]
        role="training target / excluded at prediction" if column==target else ("prediction input" if column in prediction_input_columns else "training source / excluded by administrator")
        input_contract.append({"name":str(column),"dtype":str(series.dtype),"required":column in prediction_input_columns,"example":samples[0] if samples else "","examples":samples,"source_order":source_columns.index(str(column)),"role":role,"meaning":column_meanings.get(str(column),""),"used_by_model":column in prediction_input_columns})
    d=forecast_features(source); dates=sorted(d.date.dropna().unique()); a=dates[int(len(dates)*.7)]; b=dates[int(len(dates)*.85)]; tr=d[d.date<a]; va=d[(d.date>=a)&(d.date<b)]; te=d[d.date>=b]
    
    # Target was captured from the administrator-selected schema before feature engineering.
    if target not in d.columns:
        raise ValueError(f"Missing target column: {target}")
    
    # Determine feature columns based on the transformed dataframe
    # forecast_features adds lag columns and date features, so we use what's available
    if feature_columns is None:
        cat=['store_id','product_id','category','region']; num=['inventory_level','units_ordered','price','dow','month','lag_1','lag_7','lag_14']
    else:
        # Use the exact administrator-selected raw columns that remain model-safe.
        # Dates drive the chronological split and are not passed as raw datetime values.
        selected=[c for c in prediction_input_columns if c in d.columns and c not in {target,'date'}]
        selected += [c for c in ('dow','month','lag_1','lag_7','lag_14') if c in d.columns and c not in selected]
        cat=[c for c in selected if not pd.api.types.is_numeric_dtype(d[c])]
        num=[c for c in selected if c not in cat and not pd.api.types.is_datetime64_any_dtype(d[c])]
    
    num=[c for c in num if c in d]; feats=cat+num
    
    # Ensure all feature columns exist in the dataframe
    missing_feats=[f for f in feats if f not in d.columns]
    if missing_feats:
        raise ValueError(f"Missing feature columns: {missing_feats}")
    
    runs=[]
    for name in algorithms:
        m=_forecast_model(name,cat,num).fit(tr[feats],tr[target]); runs.append({'algorithm':name,'model':m,'validation':regression(va[target],m.predict(va[feats])),'test':regression(te[target],m.predict(te[feats])),'features':feats,'raw_features':prediction_input_columns,'prediction_input_columns':prediction_input_columns,'training_source_columns':source_columns,'input_contract':input_contract,'numeric_features':num,'categorical_features':cat,'target':target,'column_meanings':column_meanings,'split':{'train':len(tr),'validation':len(va),'test':len(te),'method':'chronological'}})
    best=min(runs,key=lambda r:r['validation']['WAPE'] if r['validation']['WAPE'] is not None else 1e99); return runs,best
