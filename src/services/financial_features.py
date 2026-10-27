from __future__ import annotations
import numpy as np
import pandas as pd


def add_revenue_cashflow_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Create auditable financial targets without inventing missing cash outflows."""
    d = df.copy()
    for c in ("units_sold", "price", "discount_amount", "refund_amount", "cash_inflow", "cash_outflow"):
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "revenue" not in d and {"units_sold", "price"}.issubset(d.columns):
        d["gross_revenue"] = d["units_sold"] * d["price"]
        d["revenue"] = d["gross_revenue"] - (d["discount_amount"].fillna(0) if "discount_amount" in d else 0) - (d["refund_amount"].fillna(0) if "refund_amount" in d else 0)
    if {"cash_inflow", "cash_outflow"}.issubset(d.columns):
        d["net_cashflow"] = d["cash_inflow"] - d["cash_outflow"]
    return d


def choose_financial_target(df: pd.DataFrame, requested: str | None = None) -> str:
    d = add_revenue_cashflow_fields(df)
    if requested and requested in d.columns:
        return requested
    for candidate in ("net_cashflow", "cash_inflow", "revenue", "net_revenue", "units_sold"):
        if candidate in d.columns and pd.to_numeric(d[candidate], errors="coerce").notna().sum() >= 30:
            return candidate
    raise ValueError("Provide revenue, cash_inflow/cash_outflow, or units_sold with price.")


def add_customer_history(df: pd.DataFrame) -> pd.DataFrame:
    """Leakage-safe history: each invoice gets only earlier customer outcomes."""
    d = df.copy()
    customer = next((c for c in ("cust_number", "customer_id", "client_id") if c in d), None)
    date = next((c for c in ("posting_date", "invoice_date", "document_create_date") if c in d), None)
    target = next((c for c in ("is_late", "default_next_month") if c in d), None)
    if not customer or not date or not target:
        return d
    d["_event_date"] = pd.to_datetime(d[date].astype(str).str.replace(r"\.0$", "", regex=True), errors="coerce")
    d = d.sort_values([customer, "_event_date"], kind="stable")
    g = d.groupby(customer, sort=False)
    d["previous_invoice_count"] = g.cumcount()
    d["previous_late_invoice_count"] = g[target].transform(lambda s: pd.to_numeric(s, errors="coerce").shift().cumsum()).fillna(0)
    d["previous_late_ratio"] = np.where(d.previous_invoice_count > 0, d.previous_late_invoice_count / d.previous_invoice_count, 0.0)
    if "total_open_amount" in d:
        amount = pd.to_numeric(d.total_open_amount, errors="coerce")
        d["previous_average_invoice_amount"] = amount.groupby(d[customer]).transform(lambda s: s.shift().expanding().mean())
        d["invoice_vs_customer_average"] = amount / d.previous_average_invoice_amount.replace(0, np.nan)
    return d.drop(columns=["_event_date"])
