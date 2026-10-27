from __future__ import annotations
import numpy as np
import pandas as pd
from src.services.financial_features import add_revenue_cashflow_fields, choose_financial_target


class FinancialForecastAgent:
    """Decision layer for revenue, cash inflow, cash outflow, and net cashflow forecasts."""
    def prepare(self, df, target=None):
        d=add_revenue_cashflow_fields(df)
        return d, choose_financial_target(d,target)

    def assess(self, actual, predicted, opening_cash=None, minimum_cash=0.0):
        out=pd.DataFrame({"actual":actual,"forecast_value":np.asarray(predicted,float)})
        out["residual"]=out.actual-out.forecast_value
        scale=max(float(out.residual.std()),1e-9)
        out["is_anomaly"]=out.residual.abs()>2*scale
        if opening_cash is not None:
            out["projected_closing_cash"]=float(opening_cash)+out.forecast_value.cumsum()
            out["cash_shortfall_risk"]=out.projected_closing_cash<float(minimum_cash)
        else:
            out["cash_shortfall_risk"]=False
        return out

    def summary(self, result, target):
        total=float(result.forecast_value.sum())
        trend="decline" if len(result)>1 and result.forecast_value.iloc[-1]<result.forecast_value.iloc[0] else "stable or improving trend"
        return {"target":target,"forecast_total":total,"trend":trend,"anomalies":int(result.is_anomaly.sum()),"cash_shortfall_periods":int(result.cash_shortfall_risk.sum()),"managerial_summary":f"Projected {target.replace('_',' ')} totals {total:,.2f}. The horizon indicates a {trend}. Review flagged exceptions before taking action."}
