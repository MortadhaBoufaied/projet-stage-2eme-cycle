from __future__ import annotations
from datetime import datetime, timezone


def build_alerts(rows, value_field="forecast_value", anomaly_field="is_anomaly"):
    alerts=[]
    for i,row in rows.iterrows():
        if bool(row.get(anomaly_field, False)):
            alerts.append({"alert_id":f"FIN-{i}","severity":"HIGH","created_at":datetime.now(timezone.utc).isoformat(),"status":"OPEN","reason":"Abnormal forecast deviation","recommended_action":"Review the underlying transactions, pricing, seasonality, and data quality.","record":str(i)})
        if bool(row.get("cash_shortfall_risk", False)):
            alerts.append({"alert_id":f"CASH-{i}","severity":"CRITICAL","created_at":datetime.now(timezone.utc).isoformat(),"status":"OPEN","reason":"Projected cash balance is below the configured minimum","recommended_action":"Accelerate collections and review deferrable outflows with an authorized manager.","record":str(i)})
    return alerts
