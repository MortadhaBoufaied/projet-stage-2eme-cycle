import numpy as np
import pandas as pd
from src.services.financial_forecast_runtime import financial_mode, forecast_alerts

def test_modes_and_decline_alert():
    assert financial_mode("net_cashflow")=="Net cashflow"
    frame=pd.DataFrame({"date":pd.date_range("2026-01-01",periods=3),"forecast_value":[100,80,70],"is_future":[True]*3})
    alerts=forecast_alerts(frame,"revenue")
    assert "Projected decline" in set(alerts["type"])

def test_negative_cashflow_alert():
    frame=pd.DataFrame({"date":pd.date_range("2026-01-01",periods=2),"forecast_value":[10,-2],"is_future":[True,True]})
    alerts=forecast_alerts(frame,"net_cashflow")
    assert "Negative net cashflow" in set(alerts["type"])
