from __future__ import annotations
import numpy as np
import pandas as pd


def financial_mode(target):
    key=str(target or "units_sold").strip().lower()
    return {"revenue":"Revenue","cash_inflow":"Cash inflow","cash_outflow":"Cash outflow","net_cashflow":"Net cashflow","units_sold":"Demand"}.get(key,key.replace("_"," ").title())


def future_projection(history, model, metadata, horizon=30):
    """Generate recursive future periods from the active model without changing its feature contract."""
    if history is None or history.empty: return pd.DataFrame()
    target=str(metadata.get("target") or "units_sold")
    features=list(metadata.get("features") or [])
    if not features: raise ValueError("The active forecast model has no saved feature contract.")
    date_col="date"
    if date_col not in history: raise ValueError("Future forecasting requires a date column.")
    d=history.copy(); d[date_col]=pd.to_datetime(d[date_col],errors="coerce"); d=d.dropna(subset=[date_col])
    if d.empty: raise ValueError("No valid observation dates are available.")
    series=[c for c in ("store_id","product_id") if c in d.columns]
    if not series: d["_series"]="all"; series=["_series"]
    value_col=target if target in d else ("units_sold" if "units_sold" in d else None)
    if value_col is None: raise ValueError(f"Future forecasting needs historical {target} values.")
    d[value_col]=pd.to_numeric(d[value_col],errors="coerce")
    residual_col="residual" if "residual" in d else None
    residual_sd=float(pd.to_numeric(d[residual_col],errors="coerce").std()) if residual_col else 0.0
    residual_sd=residual_sd if np.isfinite(residual_sd) else 0.0
    rows=[]
    for keys,g in d.sort_values(date_col).groupby(series,dropna=False,sort=False):
        g=g.copy(); latest=g.iloc[-1].copy(); values=pd.to_numeric(g[value_col],errors="coerce").fillna(0).tolist()
        last_date=g[date_col].max(); keys=keys if isinstance(keys,tuple) else (keys,)
        for step in range(1,int(horizon)+1):
            row=latest.copy(); future_date=last_date+pd.Timedelta(days=step); row[date_col]=future_date
            row["dow"]=future_date.dayofweek; row["month"]=future_date.month
            for lag in (1,7,14): row[f"lag_{lag}"]=values[-lag] if len(values)>=lag else (values[0] if values else 0.0)
            X=pd.DataFrame([{f:row.get(f,np.nan) for f in features}])
            prediction=max(0.0,float(model.predict(X)[0])); values.append(prediction)
            out={"date":future_date,"forecast_value":prediction,"forecast_lower":max(0.0,prediction-1.96*residual_sd),"forecast_upper":prediction+1.96*residual_sd,"is_future":True,"forecast_mode":financial_mode(target)}
            for name,value in zip(series,keys):
                if name!="_series": out[name]=value
            for c in ("category","region","inventory_level","price","business_code"):
                if c in row: out[c]=row[c]
            rows.append(out)
    return pd.DataFrame(rows)


def forecast_alerts(frame, target=None):
    """Create user-facing financial alerts from historical exceptions and future trend/shortfall signals."""
    if frame is None or frame.empty: return pd.DataFrame(columns=["severity","type","period","reason","recommended_action","status"])
    alerts=[]
    for _,r in frame.iterrows():
        period=str(pd.to_datetime(r.get("date"),errors="coerce").date()) if pd.notna(pd.to_datetime(r.get("date"),errors="coerce")) else "Unknown"
        if bool(r.get("is_anomaly",False)):
            alerts.append({"severity":"HIGH","type":"Abnormal pattern","period":period,"reason":"Actual performance differs materially from the model expectation.","recommended_action":"Review transactions, pricing, seasonality, and source-data quality.","status":"OPEN"})
        if bool(r.get("stockout_risk",False)):
            alerts.append({"severity":"HIGH","type":"Stock exposure","period":period,"reason":"Available inventory is below the configured forecast coverage level.","recommended_action":"Review replenishment constraints and safety-stock policy with an authorized manager.","status":"OPEN"})
    future=frame[frame.get("is_future",False).fillna(False)] if "is_future" in frame else pd.DataFrame()
    if len(future)>=2:
        grouped=future.groupby("date",as_index=False).forecast_value.sum().sort_values("date")
        first=float(grouped.forecast_value.iloc[0]); last=float(grouped.forecast_value.iloc[-1])
        if first>0 and last < first*0.9:
            alerts.append({"severity":"MEDIUM","type":"Projected decline","period":str(grouped.date.iloc[-1].date()),"reason":f"Projected {financial_mode(target)} declines by more than 10% across the selected horizon.","recommended_action":"Review the main business drivers and prepare a manager-approved mitigation plan.","status":"OPEN"})
        if str(target)=="net_cashflow" and (grouped.forecast_value<0).any():
            alerts.append({"severity":"CRITICAL","type":"Negative net cashflow","period":str(grouped.loc[grouped.forecast_value.idxmin(),"date"].date()),"reason":"At least one projected period has negative net cashflow.","recommended_action":"Review collection timing and deferrable outflows with the accountable finance manager.","status":"OPEN"})
    return pd.DataFrame(alerts).drop_duplicates() if alerts else pd.DataFrame(columns=["severity","type","period","reason","recommended_action","status"])
