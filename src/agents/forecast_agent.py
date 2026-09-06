from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
try:
    from xgboost import XGBRegressor
except Exception:
    XGBRegressor = None
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.config import RANDOM_STATE

class CashflowForecastAgent:
    cat_cols=["category","region","weather_conditions","store_id","product_id"]
    def __init__(self, model_type="boosted"):
        self.model_type=model_type; self.model=None; self.feature_names=[]
    def create_features(self, df):
        d=df.copy()
        defaults={"category":"Unknown","region":"Unknown","weather_conditions":"Unknown","inventory_level":0.0,"promotions_holidays":0.0}
        for column,value in defaults.items():
            if column not in d:d[column]=value
            else:d[column]=d[column].fillna(value)
        d["date"]=pd.to_datetime(d["date"],errors="coerce"); d=d.sort_values(["store_id","product_id","date"]).copy()
        d["day_of_week"]=d.date.dt.dayofweek; d["month"]=d.date.dt.month; d["day_of_year"]=d.date.dt.dayofyear; d["is_weekend"]=(d.day_of_week>=5).astype(int)
        g=d.groupby(["store_id","product_id"],sort=False)["units_sold"]
        for lag in [1,7,14,30]: d[f"lag_{lag}"]=g.shift(lag)
        for win in [7,14,30]:
            d[f"roll_mean_{win}"]=g.transform(lambda s:s.shift(1).rolling(win,min_periods=1).mean())
            d[f"roll_std_{win}"]=g.transform(lambda s:s.shift(1).rolling(win,min_periods=2).std())
        return d
    def fit(self, featured_train_df):
        d=featured_train_df.copy()
        self.feature_names=self.cat_cols+["inventory_level","promotions_holidays","day_of_week","month","day_of_year","is_weekend"]+[c for c in d.columns if c.startswith("lag_") or c.startswith("roll_")]
        X=d[self.feature_names]; y=d["units_sold"].astype(float)
        numeric=[c for c in self.feature_names if c not in self.cat_cols]
        pre=ColumnTransformer([("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore"))]),self.cat_cols),("num",Pipeline([("imp",SimpleImputer(strategy="median")),("scale",StandardScaler(with_mean=False))]),numeric)])
        if self.model_type == "xgboost":
            if XGBRegressor is None:
                raise RuntimeError("xgboost is required for the cashflow model. Install project requirements.")
            model=XGBRegressor(n_estimators=500,learning_rate=.035,max_depth=7,subsample=.9,colsample_bytree=.9,objective="reg:squarederror",random_state=RANDOM_STATE,n_jobs=-1)
        elif self.model_type == "baseline":
            model=Ridge(alpha=1.0)
        else:
            model=HistGradientBoostingRegressor(max_iter=300,learning_rate=.04,max_depth=7,random_state=RANDOM_STATE)
        if self.model_type in {"boosted", "xgboost"}:
            pre=ColumnTransformer([("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore",sparse_output=True))]),self.cat_cols),("num",SimpleImputer(strategy="median"),numeric)])
        self.model=Pipeline([("pre",pre),("model",model)]).fit(X,y); return self
    def predict_featured(self, featured_df): return np.clip(self.model.predict(featured_df[self.feature_names]),0,None)
    def evaluate_featured(self, featured_test_df):
        y=featured_test_df["units_sold"].astype(float).to_numpy(); p=self.predict_featured(featured_test_df)
        mae=float(mean_absolute_error(y,p)); rmse=float(mean_squared_error(y,p)**.5); denom=float(np.abs(y).sum())
        return {"MAE":round(mae,4),"RMSE":round(rmse,4),"WAPE":round(float(np.abs(y-p).sum()/denom),4) if denom else None,"R2":round(float(r2_score(y,p)),4),"n_test":int(len(y))}
    def predict_historical(self, df):
        f=self.create_features(df); f["forecast_units_sold"]=np.round(self.predict_featured(f),2); return f
    def detect_anomalies(self, df):
        r=self.predict_historical(df); r["residual"]=r["units_sold"]-r["forecast_units_sold"]; scale=max(float(r.residual.std()),1e-6)
        r["is_anomaly"]=(r.residual.abs()>2*scale).astype(int); r["is_stockout_risk"]=(r.inventory_level<2*r.forecast_units_sold).astype(int); return r
