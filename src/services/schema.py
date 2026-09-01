from __future__ import annotations
from difflib import SequenceMatcher
import re
import pandas as pd

PAY_STATUS_FIELDS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
CREDIT_FEATURES = (["LIMIT_BAL", "AGE", "EDUCATION", "MARRIAGE"] + PAY_STATUS_FIELDS +
                   [f"BILL_AMT{i}" for i in range(1, 7)] + [f"PAY_AMT{i}" for i in range(1, 7)])
CREDIT_TARGET = "default_next_month"
CREDIT_ID = "client_id"
FORECAST_FIELDS = ["date", "store_id", "product_id", "category", "region", "units_sold",
                   "inventory_level", "promotions_holidays", "weather_conditions"]
ALIASES = {
    CREDIT_ID: {"id", "clientid", "customerid", "accountid", "customer_id", "client_id"},
    CREDIT_TARGET: {"defaultpaymentnextmonth", "default_next_month", "defaultnextmonth", "target", "default"},
}

def _norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())

def _family(value):
    n = _norm(value)
    if n in {"pay0", "pay2", "pay3", "pay4", "pay5", "pay6"}: return "PAY_STATUS"
    if re.fullmatch(r"payamt[1-6]", n): return "PAYMENT_AMOUNT"
    if re.fullmatch(r"billamt[1-6]", n): return "BILL_AMOUNT"
    if n in {_norm(x) for x in ALIASES[CREDIT_ID]}: return "IDENTIFIER"
    if n in {_norm(x) for x in ALIASES[CREDIT_TARGET]}: return "TARGET"
    return "GENERAL"

def _compatible(canonical, source):
    family = _family(canonical)
    return family == "GENERAL" or family == _family(source)

def available_credit_fields(columns, require_target=True):
    """Return the model contract. ID is included only when the upload has an ID-like column."""
    normalized = {_norm(c) for c in columns}
    has_id = bool(normalized & {_norm(x) for x in ALIASES[CREDIT_ID]})
    return ([CREDIT_ID] if has_id else []) + CREDIT_FEATURES + ([CREDIT_TARGET] if require_target else [])

def suggest_mapping(columns, required):
    """Map only real uploaded columns. No source/business column is ever generated."""
    columns = list(columns); result = {field: "" for field in required}; used = set()
    normalized = {column: _norm(column) for column in columns}
    # Pass 1 reserves all exact matches globally, preventing PAY_AMT/PAY collisions.
    for field in required:
        match = next((c for c in columns if c not in used and normalized[c] == _norm(field)), None)
        if match: result[field] = match; used.add(match)
    # Pass 2 accepts explicit aliases only.
    for field in required:
        if result[field]: continue
        aliases = {_norm(x) for x in ALIASES.get(field, set())}
        match = next((c for c in columns if c not in used and normalized[c] in aliases), None)
        if match: result[field] = match; used.add(match)
    # Pass 3 is conservative and family-safe. PAY fields require exact matching.
    for field in required:
        if result[field] or _family(field) in {"PAY_STATUS", "PAYMENT_AMOUNT", "BILL_AMOUNT"}: continue
        ranked = sorted(((SequenceMatcher(None, _norm(field), normalized[c]).ratio(), c)
                         for c in columns if c not in used and _compatible(field, c)), reverse=True)
        if ranked and ranked[0][0] >= .92: result[field] = ranked[0][1]; used.add(ranked[0][1])
    return result

def mapping_diagnostics(mapping, required=None):
    required = required or list(mapping); selected = [v for v in mapping.values() if v]; errors = []; rows = []
    duplicates = sorted({v for v in selected if selected.count(v) > 1})
    if duplicates: errors.append("One source column cannot map to multiple fields: " + ", ".join(duplicates))
    for field in required:
        source = mapping.get(field, "")
        if not source:
            status, confidence = ("Optional", 0.0) if field == CREDIT_ID else ("Missing", 0.0)
            if field != CREDIT_ID: errors.append(f"Required field is not mapped: {field}")
        elif not _compatible(field, source):
            status, confidence = "Invalid family", 0.0; errors.append(f"Incompatible mapping: {field} cannot use {source}")
        elif _norm(field) == _norm(source): status, confidence = "Exact", 1.0
        elif _norm(source) in {_norm(x) for x in ALIASES.get(field, set())}: status, confidence = "Alias", .98
        else: status, confidence = "Suggested", SequenceMatcher(None, _norm(field), _norm(source)).ratio()
        rows.append({"System field": field, "Source column": source or "Not mapped", "Status": status, "Confidence": confidence})
    return rows, list(dict.fromkeys(errors))

def mapping_errors(mapping): return mapping_diagnostics(mapping)[1]

def apply_mapping(df, mapping):
    """Rename mapped uploaded columns only. Never synthesize source or business fields."""
    return df.rename(columns={source: field for field, source in mapping.items() if source}).copy()

def validate_credit(df, require_target=True):
    required = CREDIT_FEATURES + ([CREDIT_TARGET] if require_target else [])
    errors = [f"Missing column: {c}" for c in required if c not in df]
    if errors: return errors
    if require_target and len(df) < 30: errors.append("Credit training data requires at least 30 rows.")
    if require_target:
        y = pd.to_numeric(df[CREDIT_TARGET], errors="coerce"); values = set(y.dropna().unique())
        if y.isna().any() or not values.issubset({0, 1}) or len(values) < 2:
            errors.append("Target must contain only 0 and 1, with both classes present.")
    bad = [c for c in CREDIT_FEATURES if pd.to_numeric(df[c], errors="coerce").isna().mean() > .20]
    if bad: errors.append("More than 20% invalid numeric values in: " + ", ".join(bad))
    age = pd.to_numeric(df.AGE, errors="coerce"); limit = pd.to_numeric(df.LIMIT_BAL, errors="coerce")
    if ((age < 18) | (age > 110)).any(): errors.append("AGE contains values outside 18 to 110.")
    if (limit < 0).any(): errors.append("LIMIT_BAL cannot be negative.")
    return errors

def validate_forecast(df, require_target=True):
    required = FORECAST_FIELDS if require_target else [c for c in FORECAST_FIELDS if c != "units_sold"]
    errors = [f"Missing column: {c}" for c in required if c not in df]
    if errors: return errors
    dates = pd.to_datetime(df.date, errors="coerce")
    if dates.isna().any(): errors.append("Some dates are invalid.")
    if dates.nunique() < 10: errors.append("At least 10 distinct dates are required.")
    if df.duplicated(["date", "store_id", "product_id"]).any(): errors.append("Duplicate date/store/product rows were found.")
    if require_target and (pd.to_numeric(df.units_sold, errors="coerce") < 0).any(): errors.append("units_sold cannot be negative.")
    return errors

def quality_report(df):
    return {"rows": len(df), "columns": len(df.columns), "duplicate_rows": int(df.duplicated().sum()),
            "missing_cells": int(df.isna().sum().sum()),
            "missing_percent": round(float(df.isna().mean().mean() * 100), 2) if len(df.columns) else 0}
