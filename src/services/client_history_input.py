from __future__ import annotations
import re
import pandas as pd
from src.services.customer_history import HISTORY_FEATURES, enrich_current, prepare_reference

RECORD_TYPE = "record_type"
HISTORY = "History"
CURRENT = "Current"
OUTCOME_FIELDS = ("clear_date", "delay_days", "is_late")


def _norm(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def find_column(frame, *names):
    by = {_norm(column): column for column in frame.columns}
    return next((by[_norm(name)] for name in names if _norm(name) in by), None)


def _customer_field(columns):
    """Use the identifier from the active training contract instead of adding a duplicate ID."""
    by_norm = {_norm(column): column for column in columns}
    for candidate in ("cust_number", "customer_id", "client_id"):
        if _norm(candidate) in by_norm:
            return by_norm[_norm(candidate)]
    return "client_id"


def editor_columns(raw_features):
    """Show the complete active-model input contract in a practical invoice-entry order."""
    raw = list(dict.fromkeys(str(value) for value in raw_features))
    customer = _customer_field(raw)
    priority_names = (
        customer, "business_code", "area_business", "buisness_year", "business_year",
        "posting_date", "document_create_date", "document_create_date.1",
        "due_in_date", "due_date", "total_open_amount", "invoice_amount",
        "invoice_currency", "document type", "document_type", "cust_payment_terms",
    )
    by_norm = {_norm(column): column for column in raw}
    ordered = []
    for name in priority_names:
        column = by_norm.get(_norm(name))
        if column is not None and column not in ordered:
            ordered.append(column)
    ordered.extend(column for column in raw if column not in ordered)
    fields = [RECORD_TYPE, *ordered, *OUTCOME_FIELDS]
    if customer not in fields:
        fields.insert(1, customer)
    return list(dict.fromkeys(fields))


def empty_editor_frame(raw_features, rows=3):
    columns = editor_columns(raw_features)
    customer = _customer_field(columns)
    data = [{column: None for column in columns} for _ in range(max(2, rows))]
    for index, row in enumerate(data):
        row[customer] = "customer_1"
        row[RECORD_TYPE] = CURRENT if index == len(data) - 1 else HISTORY
    return pd.DataFrame(data, columns=columns)


def prepare_history_assessment(frame, model_features):
    """Return current invoices enriched only with outcomes known before their posting date."""
    if frame is None or frame.empty:
        raise ValueError("Add at least one payment record.")
    data = frame.copy().dropna(how="all").reset_index(drop=True)
    data = data.loc[~data.astype("string").fillna("").apply(lambda row: row.str.strip().eq("").all(), axis=1)].copy()
    if data.empty:
        raise ValueError("Add at least one payment record.")
    customer = find_column(data, "cust_number", "customer_id", "client_id")
    if not customer:
        raise ValueError("The table needs a customer identifier such as cust_number or client_id.")
    if RECORD_TYPE not in data:
        data[RECORD_TYPE] = HISTORY
        data.loc[data.groupby(customer, dropna=False).tail(1).index, RECORD_TYPE] = CURRENT
    kinds = data[RECORD_TYPE].astype("string").str.strip().str.lower()
    invalid = ~kinds.isin({"history", "current"})
    if invalid.any():
        raise ValueError("Record Type must be History or Current.")
    current = data.loc[kinds.eq("current")].copy()
    history = data.loc[kinds.eq("history")].copy()
    if current.empty:
        raise ValueError("Mark at least one row as Current. Current rows are the invoices to assess.")
    required = [feature for feature in model_features if feature not in HISTORY_FEATURES]
    missing_columns = [feature for feature in required if feature not in current.columns]
    if missing_columns:
        raise ValueError("Missing current-invoice columns: " + ", ".join(missing_columns))
    blank = []
    for feature in required:
        values = current[feature]
        if values.isna().any() or values.astype("string").str.strip().eq("").any():
            blank.append(feature)
    if blank:
        raise ValueError("Complete these fields for every Current row: " + ", ".join(blank))
    reference = prepare_reference(history)
    enriched = enrich_current(current, reference)
    enriched = enriched.drop(columns=[RECORD_TYPE], errors="ignore")
    stats = {
        "history_rows": int(len(history)),
        "current_rows": int(len(current)),
        "customers": int(data[customer].astype("string").nunique()),
        "history_used": bool(len(reference)),
        "model_uses_history": bool(set(model_features) & set(HISTORY_FEATURES)),
    }
    return enriched, stats
