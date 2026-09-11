from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from lightgbm import LGBMRegressor
from src.config import RANDOM_STATE

AVAILABLE_FORECAST_MODELS = {"boosted", "baseline", "lightgbm", "randomforest"}

DEFAULT_FORECAST_HYPERPARAMS = {
    "boosted": {"max_iter": 300, "learning_rate": 0.04, "max_depth": 7, "l2_regularization": 1.0},
    "lightgbm": {"n_estimators": 500, "max_depth": 6, "learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 20, "subsample": 0.85, "colsample_bytree": 0.85, "reg_alpha": 0.1, "reg_lambda": 1.5},
    "randomforest": {"n_estimators": 500, "max_depth": 15, "min_samples_split": 5, "min_samples_leaf": 2},
    "baseline": {"alpha": 1.0},
}

class CashflowForecastAgent:
    cat_cols=["category","region","weather_conditions","store_id","product_id"]
    def __init__(self, model_type="boosted", hyperparams=None):
        self.model_type=model_type; self.hyperparams=hyperparams or {}; self.model=None; self.feature_names=[]
    def create_features(self, df):
        d=df.copy(); d["date"]=pd.to_datetime(d["date"],errors="coerce"); d=d.sort_values(["store_id","product_id","date"]).copy()
        d["day_of_week"]=d.date.dt.dayofweek; d["month"]=d.date.dt.month; d["day_of_year"]=d.date.dt.dayofyear; d["is_weekend"]=(d.day_of_week>=5).astype(int)
        g=d.groupby(["store_id","product_id"],sort=False)["units_sold"]
        for lag in [1,7,14,30]: d[f"lag_{lag}"]=g.shift(lag)
        for win in [7,14,30]:
            d[f"roll_mean_{win}"]=g.transform(lambda s:s.shift(1).rolling(win,min_periods=1).mean())
            d[f"roll_std_{win}"]=g.transform(lambda s: s.shift(1).rolling(win,min_periods=2).std())
        return d
    def fit(self, featured_train_df):
        d=featured_train_df.copy()
        self.feature_names=self.cat_cols+["inventory_level","promotions_holidays","day_of_week","month","day_of_year","is_weekend"]+[c for c in d.columns if c.startswith("lag_") or c.startswith("roll_")]
        X=d[self.feature_names]; y=d["units_sold"].astype(float)
        numeric=[c for c in self.feature_names if c not in self.cat_cols]
        self._build_model(X,y,numeric); return self
    def _build_model(self, X, y, numeric):
        hp=self.hyperparams; base=DEFAULT_FORECAST_HYPERPARAMS[self.model_type]
        merged={**base, **hp}
        if self.model_type=="baseline":
            model=Ridge(alpha=merged.get("alpha",1.0))
        elif self.model_type=="boosted":
            model=HistGradientBoostingRegressor(max_iter=merged.get("max_iter",300),learning_rate=merged.get("learning_rate",0.04),max_depth=merged.get("max_depth",7),random_state=RANDOM_STATE)
        elif self.model_type=="lightgbm":
            model=LGBMRegressor(n_estimators=merged.get("n_estimators",500),max_depth=merged.get("max_depth",6),learning_rate=merged.get("learning_rate",0.03),num_leaves=merged.get("num_leaves",31),min_child_samples=merged.get("min_child_samples",20),subsample=merged.get("subsample",0.85),colsample_bytree=merged.get("colsample_bytree",0.85),reg_alpha=merged.get("reg_alpha",0.1),reg_lambda=merged.get("reg_lambda",1.5),random_state=RANDOM_STATE,n_jobs=-1,verbose=-1)
        else:
            model=RandomForestRegressor(n_estimators=merged.get("n_estimators",500),max_depth=merged.get("max_depth",15),min_samples_split=merged.get("min_samples_split",5),min_samples_leaf=merged.get("min_samples_leaf",2),random_state=RANDOM_STATE,n_jobs=-1)
        pre=ColumnTransformer([("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore",sparse_output=False))]),self.cat_cols),("num",SimpleImputer(strategy="median"),numeric)]) if self.model_type=="lightgbm" else ColumnTransformer([("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore"))]),self.cat_cols),("num",Pipeline([("imp",SimpleImputer(strategy="median")),("scale",StandardScaler(with_mean=False))]),numeric)])
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

    def predict_forward(self, df, n_periods=14):
        """Iterative multi-step forecast projecting n_periods into the future.

        Takes the most recent historical data, builds features, then
        repeatedly predicts the next period and feeds the prediction back
        as a lag value for subsequent predictions.

        Args:
            df: Historical demand DataFrame with at least date, store_id,
                product_id, units_sold, and inventory columns.
            n_periods: Number of future periods to project (default 14).

        Returns:
            DataFrame with projected dates, predicted units, and the
            iterative step number (1 = first future period).
        """
        import pandas as pd
        import numpy as np

        featured = self.create_features(df)
        featured = featured.sort_values(["store_id", "product_id", "date"]).copy()

        # Take the last row per group as the seed for iterative prediction
        last_rows = featured.groupby(["store_id", "product_id"], sort=False).tail(1).copy()
        projections = []

        for _, seed in last_rows.iterrows():
            current = seed.copy()
            for step in range(1, n_periods + 1):
                # Build a single-row DataFrame matching the model's expected features
                row_df = pd.DataFrame([current])[self.feature_names]
                pred = float(np.clip(self.model.predict(row_df)[0], 0, None))

                # Advance the date by one day
                next_date = current["date"] + pd.Timedelta(days=1)

                # Update lag features by shifting: lag_1 becomes the prediction
                for lag in [1, 7, 14, 30]:
                    col = f"lag_{lag}"
                    if lag == 1:
                        current[col] = pred
                    elif col in current.index:
                        # For longer lags, keep the previous value (no new data)
                        pass

                # Update rolling means using the new prediction
                for win in [7, 14, 30]:
                    mean_col = f"roll_mean_{win}"
                    if mean_col in current.index:
                        # Approximate: blend the prediction into the rolling mean
                        old_mean = current[mean_col] if pd.notna(current[mean_col]) else pred
                        current[mean_col] = (old_mean * (win - 1) + pred) / win

                # Update time features
                current["date"] = next_date
                current["day_of_week"] = next_date.dayofweek
                current["month"] = next_date.month
                current["day_of_year"] = next_date.dayofyear
                current["is_weekend"] = 1 if next_date.dayofweek >= 5 else 0

                projections.append({
                    "date": next_date,
                    "store_id": current["store_id"],
                    "product_id": current["product_id"],
                    "predicted_units": round(pred, 2),
                    "step": step,
                })

        return pd.DataFrame(projections)

    def predict_revenue(self, predictions_df, price_per_unit=1.0):
        """Multiply predicted units by a per-unit price to produce revenue estimates.

        Args:
            predictions_df: DataFrame with a 'predicted_units' column
                (output of predict_forward or predict_historical).
            price_per_unit: Monetary value per unit. Default 1.0 means
                revenue equals units (pure demand view).

        Returns:
            Same DataFrame with an added 'estimated_revenue' column.
        """
        df = predictions_df.copy()
        df["estimated_revenue"] = (df["predicted_units"] * price_per_unit).round(2)
        return df


def compute_forecast_composite_score(metrics):
    mae=metrics.get("MAE",999); rmse=metrics.get("RMSE",999); r2=metrics.get("R2",0); wape=metrics.get("WAPE",0) or 0
    return (r2 * 2 - (mae + rmse) / 100 - wape) / 4.0


def get_best_forecast_model(models_metrics):
    best=None; best_score=-999
    for name,metrics in models_metrics.items():
        score=compute_forecast_composite_score(metrics)
        if score>best_score: best_score=score; best=name
    return best,best_score
