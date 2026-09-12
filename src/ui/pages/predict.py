"""Single-record prediction page for testing individual customers or demand records.

Allows companies to enter one record manually (or search an existing customer
by client_id) and get an instant risk score, forecast, SHAP explanation,
and governance-filtered recommendation without uploading a CSV.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.schema import (
    CREDIT_FEATURES,
    CREDIT_ID,
    CREDIT_TARGET,
    FORECAST_FIELDS,
    available_credit_fields,
)
from src.services.recommendation_policy import RecommendationPolicy
from src.services.explainer import compute_shap_values
from src.services.nlg import generate_credit_summary, generate_demand_summary
from src.ui.components.display import metric_cards, render_shap_bar, render_shap_table, risk_tier_badge
from src.ui.components.fields import model_select_from_registry


# ---------------------------------------------------------------------------
# Credit feature input helpers
# ---------------------------------------------------------------------------

# Human-readable labels for each credit feature field
CREDIT_FIELD_LABELS = {
    "LIMIT_BAL": "Credit limit (LIMIT_BAL)",
    "AGE": "Age",
    "EDUCATION": "Education level",
    "MARRIAGE": "Marriage status",
    "PAY_0": "Payment status (Month M - latest)",
    "PAY_2": "Payment status (Month M-1)",
    "PAY_3": "Payment status (Month M-2)",
    "PAY_4": "Payment status (Month M-3)",
    "PAY_5": "Payment status (Month M-4)",
    "PAY_6": "Payment status (Month M-5)",
    "BILL_AMT1": "Bill statement (Month M - latest)",
    "BILL_AMT2": "Bill statement (Month M-1)",
    "BILL_AMT3": "Bill statement (Month M-2)",
    "BILL_AMT4": "Bill statement (Month M-3)",
    "BILL_AMT5": "Bill statement (Month M-4)",
    "BILL_AMT6": "Bill statement (Month M-5)",
    "PAY_AMT1": "Amount paid (Month M - latest)",
    "PAY_AMT2": "Amount paid (Month M-1)",
    "PAY_AMT3": "Amount paid (Month M-2)",
    "PAY_AMT4": "Amount paid (Month M-3)",
    "PAY_AMT5": "Amount paid (Month M-4)",
    "PAY_AMT6": "Amount paid (Month M-5)",
    "default_next_month": "Default payment next month (target)",
    "client_id": "Client ID",
}

CREDIT_SELECT_FIELDS = {"EDUCATION", "MARRIAGE", "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"}

EDUCATION_OPTIONS = ["Unknown", "Primary school", "Secondary school", "High school", "University"]
MARRIAGE_OPTIONS = ["Married", "Single", "Others"]
PAY_OPTIONS = ["-2", "-1", "0", "1", "2", "3", "4", "5", "6", "8"]

CREDIT_INPUT_ORDER = [
    CREDIT_ID,
    "LIMIT_BAL", "AGE", "EDUCATION", "MARRIAGE",
    "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
    "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
    CREDIT_TARGET,
]


def _numeric_input(key: str, label: str, default: float = 0.0) -> float:
    """Render a Streamlit number input and return the value."""
    return st.number_input(label, min_value=-1e9, max_value=1e9, value=default, step=1.0, key=key)


def _select_input(key: str, label: str, options: list[str], default: str) -> str:
    """Render a Streamlit select input and return the value."""
    return st.selectbox(label, options=options, index=options.index(default) if default in options else 0, key=key)


def _build_credit_record() -> pd.DataFrame:
    """Render inputs for every credit feature with friendly labels organized by category."""
    st.markdown("#### Customer profile & account details")
    st.caption("Fill in the fields below. The active credit model will score this customer.")

    values: dict[str, float | str] = {}

    # Section 1: Demographics & Account Info
    st.markdown("##### Demographics & General Info")
    col1, col2, col3 = st.columns(3)
    with col1:
        values[CREDIT_ID] = st.text_input(
            CREDIT_FIELD_LABELS.get(CREDIT_ID, "Client ID"),
            value="",
            help="Optional unique identifier for this customer.",
            key="pred_client_id",
        )
        values["EDUCATION"] = _select_input(
            "pred_education",
            CREDIT_FIELD_LABELS["EDUCATION"],
            EDUCATION_OPTIONS,
            "Unknown",
        )
    with col2:
        values["LIMIT_BAL"] = _numeric_input(
            "pred_limit_bal",
            CREDIT_FIELD_LABELS["LIMIT_BAL"],
            default=0.0,
        )
        values["MARRIAGE"] = _select_input(
            "pred_marriage",
            CREDIT_FIELD_LABELS["MARRIAGE"],
            MARRIAGE_OPTIONS,
            "Single",
        )
    with col3:
        values["AGE"] = _numeric_input(
            "pred_age",
            CREDIT_FIELD_LABELS["AGE"],
            default=0.0,
        )
        values[CREDIT_TARGET] = _select_input(
            "pred_target",
            CREDIT_FIELD_LABELS["default_next_month"],
            ["0", "1"],
            "0",
        )

    # Section 2: Repayment Status (Months M to M-5)
    st.markdown("##### Repayment status history (last 6 months)")
    st.caption(
        "Chronological status from most recent (Month M) to 5 months prior (Month M-5). "
        "Codes: -2 = no consumption, -1 = paid in full, 0 = revolving credit, 1..8 = months payment delayed."
    )
    pay_cols = st.columns(6)
    pay_fields = [
        ("Month M (latest)", "PAY_0"),
        ("Month M-1", "PAY_2"),
        ("Month M-2", "PAY_3"),
        ("Month M-3", "PAY_4"),
        ("Month M-4", "PAY_5"),
        ("Month M-5", "PAY_6"),
    ]
    for col, (label_title, field) in zip(pay_cols, pay_fields):
        with col:
            values[field] = _select_input(
                f"pred_{field.lower()}",
                label_title,
                PAY_OPTIONS,
                "0",
            )

    # Section 3: Monthly Billing & Payments Side-by-Side
    st.markdown("##### Statement & payment history (last 6 months)")
    st.caption("Pair each month's billed statement against the amount paid (e.g. Month M = most recent closed period).")
    months = [
        ("Month M (latest closed)", "BILL_AMT1", "PAY_AMT1"),
        ("Month M-1", "BILL_AMT2", "PAY_AMT2"),
        ("Month M-2", "BILL_AMT3", "PAY_AMT3"),
        ("Month M-3", "BILL_AMT4", "PAY_AMT4"),
        ("Month M-4", "BILL_AMT5", "PAY_AMT5"),
        ("Month M-5", "BILL_AMT6", "PAY_AMT6"),
    ]

    bill_cols = st.columns(3)
    for idx, (month_name, bill_field, pay_field) in enumerate(months):
        target_col = bill_cols[idx % 3]
        with target_col:
            st.markdown(f"**{month_name}**")
            values[bill_field] = _numeric_input(
                f"pred_{bill_field.lower()}",
                "Billed statement",
                default=0.0,
            )
            values[pay_field] = _numeric_input(
                f"pred_{pay_field.lower()}",
                "Amount paid",
                default=0.0,
            )

    # Construct single-row DataFrame with numeric types for all financial fields
    row: dict[str, object] = {}
    for field, val in values.items():
        if field in CREDIT_SELECT_FIELDS or field in (CREDIT_TARGET,):
            # Convert payment/bill/numeric select fields to float
            try:
                row[field] = float(val)
            except (ValueError, TypeError):
                row[field] = val
        elif field == CREDIT_ID:
            row[field] = str(val) if val else None
        else:
            row[field] = val

    df = pd.DataFrame([row])
    return df


# Friendly labels for forecast fields
FORECAST_FIELD_LABELS = {
    "date": "Date (YYYY-MM-DD)",
    "store_id": "Store ID",
    "product_id": "Product ID",
    "category": "Category",
    "region": "Region",
    "units_sold": "Units sold (for evaluation)",
    "inventory_level": "Inventory level",
    "promotions_holidays": "Promotions/holidays",
    "weather_conditions": "Weather conditions",
}


def _build_forecast_record() -> pd.DataFrame:
    """Render inputs for every forecast field with friendly labels and return a single-row DataFrame."""
    st.markdown("#### Period & store details")
    st.caption("Fill in the fields for a single period. The active forecast model will predict demand.")

    values: dict[str, object] = {}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Period & location")
        values["date"] = st.text_input(
            FORECAST_FIELD_LABELS["date"],
            value="2026-01-01",
            help="Date in YYYY-MM-DD format.",
            key="pred_date",
        )
        values["store_id"] = st.text_input(
            FORECAST_FIELD_LABELS["store_id"],
            value="",
            key="pred_store_id",
        )
        values["product_id"] = st.text_input(
            FORECAST_FIELD_LABELS["product_id"],
            value="",
            key="pred_product_id",
        )
        values["category"] = st.text_input(
            FORECAST_FIELD_LABELS["category"],
            value="",
            key="pred_category",
        )
        values["region"] = st.text_input(
            FORECAST_FIELD_LABELS["region"],
            value="",
            key="pred_region",
        )

    with col2:
        st.markdown("##### Stock, weather & promotions")
        values["inventory_level"] = _numeric_input(
            "pred_inventory_level",
            FORECAST_FIELD_LABELS["inventory_level"],
            default=0.0,
        )
        values["promotions_holidays"] = st.selectbox(
            FORECAST_FIELD_LABELS["promotions_holidays"],
            ["No", "Yes"],
            index=0,
            key="pred_promotions_holidays",
        )
        values["weather_conditions"] = st.text_input(
            FORECAST_FIELD_LABELS["weather_conditions"],
            value="",
            key="pred_weather_conditions",
        )
        values["units_sold"] = _numeric_input(
            "pred_units_sold",
            FORECAST_FIELD_LABELS["units_sold"],
            default=0.0,
        )

    row = {k: v for k, v in values.items()}
    df = pd.DataFrame([row])
    return df


# ---------------------------------------------------------------------------
# Result display helpers
# ---------------------------------------------------------------------------

def _display_credit_result(result_df: pd.DataFrame, shap_results: list | None, company: str) -> None:
    """Display single-record credit prediction results."""
    if result_df is None or result_df.empty:
        return

    rec = result_df.iloc[0]

    st.markdown("#### Result")
    metric_cards(
        {
            "risk_score": float(rec["risk_score"]),
            "tier": rec["risk_tier"],
        },
        ["risk_score", "tier"],
    )

    # Standardized risk tier badge
    risk_tier_badge(rec["risk_tier"], float(rec["risk_score"]))

    # Key indicators
    key_inds = rec.get("key_indicators", "")
    if key_inds:
        st.markdown("**Key risk indicators:**")
        st.write(key_inds)

    # Recommended actions
    actions = rec.get("recommended_actions", "")
    if actions:
        st.markdown("**Recommended actions:**")
        st.write(actions)

    # SHAP explainability
    if shap_results is not None and len(shap_results) > 0:
        indicators = shap_results[0]
        st.markdown("#### SHAP explanation")
        st.caption("Feature contributions for this customer. Positive = increases risk.")
        render_shap_bar(indicators, record_label=str(rec.get(CREDIT_ID, "customer")), key_prefix="pred_credit_shap")
        with st.expander("SHAP details"):
            render_shap_table(indicators)

    # AI Summary
    st.markdown("#### AI Summary")
    records_for_nlg = result_df.to_dict(orient="records")
    model_type = st.session_state.get(f"credit_model_type_{company}", "N/A")
    nlg_metrics = {"model_type": model_type}
    cached = st.session_state.get(f"credit_eval_metrics_{company}")
    if isinstance(cached, dict):
        nlg_metrics.update(cached)
    summary_text = generate_credit_summary(records_for_nlg, nlg_metrics)
    st.markdown(summary_text)


def _display_forecast_result(result_df: pd.DataFrame, shap_results: list | None, company: str) -> None:
    """Display single-record demand forecast results."""
    if result_df is None or result_df.empty:
        return

    st.markdown("#### Forecast result")
    st.dataframe(result_df, width='stretch', hide_index=True)

    # SHAP explainability
    if shap_results is not None and len(shap_results) > 0:
        indicators = shap_results[0]
        st.markdown("#### SHAP explanation")
        st.caption("Feature contributions for this period.")
        render_shap_bar(indicators, record_label=str(result_df.iloc[0].get("date", "")), key_prefix="pred_forecast_shap")
        with st.expander("SHAP details"):
            render_shap_table(indicators)

    # AI Summary
    st.markdown("#### AI Summary")
    model_type = st.session_state.get(f"forecast_model_type_{company}", "N/A")
    n_anomalies = int(result_df.iloc[0].get("is_anomaly", 0))
    n_stockouts = int(result_df.iloc[0].get("is_stockout_risk", 0))
    summary_text = generate_demand_summary({}, n_anomalies, n_stockouts, model_type)
    st.markdown(summary_text)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(registry, recommender, profiles, company) -> None:
    """Render the single-record prediction page."""

    st.markdown(
        '<div class="page-header"><h1>Single-record Decision Simulation</h1>'
        '<p class="lead">Test a single customer, invoice, or period record against the active AI agents. '
        'Enter attributes directly or look up an existing record to generate probability scores, demand forecasts, '
        'SHAP explanations, and governance-filtered managerial actions.</p></div>',
        unsafe_allow_html=True,
    )
    st.info(
        "This tool allows credit managers and financial officers to test individual customer applications, "
        "invoice terms, or demand periods against the active model before committing decisions to the ERP system."
    )

    # Tabs: Credit risk / Demand forecast
    tab_credit, tab_demand = st.tabs(["Credit risk", "Demand forecast"])

    # -- Credit risk tab ---------------------------------------------------
    with tab_credit:
        # Search section
        st.markdown("#### Search existing customer or invoice")
        search_id = st.text_input("Enter Client ID / Invoice Ref to search", key="pred_search_id", help="Optional: look up a customer or invoice from the latest uploaded dataset.")

        # Build the input form
        credit_df = _build_credit_record()

        # Model selection (for when no search result)
        selected_model_meta = model_select_from_registry(
            registry, company, "credit",
            key="pred_model",
            label="Model type (override)",
        )

        if st.button("Score customer", type="primary", key="pred_score_credit"):
            try:
                with st.status("Scoring customer...", expanded=True) as status:
                    # Load the selected model version (defaults to active)
                    if selected_model_meta:
                        version, source_company = selected_model_meta
                        model, _ = registry.load_by_version(source_company, "credit", version)
                    else:
                        model, _ = registry.load_latest_with_admin_fallback(company, "credit")

                    # If a search ID was provided, try to find a matching record
                    if search_id:
                        search_df = pd.DataFrame({CREDIT_ID: [search_id]})
                        merged = pd.concat([search_df, credit_df], axis=1)
                        merged = merged.drop(columns=[c for c in merged.columns if c not in available_credit_fields(credit_df.columns, False)], errors="ignore")
                    else:
                        merged = credit_df

                    # Ensure all required fields exist with proper types
                    required = available_credit_fields(merged.columns, False)
                    for f in required:
                        if f not in merged.columns:
                            merged[f] = 0.0

                    # Reorder columns to match required fields
                    merged = merged[required]
                    # Convert numeric columns
                    for col in merged.columns:
                        if col != CREDIT_ID and col in CREDIT_FEATURES:
                            merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0.0)

                    p, tiers = model.predict_risk(merged)
                    explanations = model.explain(merged)
                    shap_results = compute_shap_values(model.model, merged, top_k=8)

                    profile = profiles.load(company)
                    policy = RecommendationPolicy()

                    identifiers = (
                        merged[CREDIT_ID].astype(str)
                        if CREDIT_ID in merged.columns
                        else merged.index.astype(str)
                    )
                    result = pd.DataFrame({
                        CREDIT_ID: identifiers,
                        "risk_score": p,
                        "risk_tier": tiers,
                    })
                    result["key_indicators"] = [
                        " | ".join(
                            f"{i['feature']}: {i['relative_position']}"
                            for i in x.get("unusual_indicators", [])
                        )
                        for x in explanations
                    ]
                    result["recommended_actions"] = [
                        " | ".join(
                            policy.apply(recommender.credit(x), profile)["recommended_actions"]
                        )
                        for x in explanations
                    ]
                    st.session_state[f"predict_credit_result_{company}"] = result
                    st.session_state[f"predict_credit_shap_{company}"] = shap_results
                    st.session_state[f"predict_credit_model_type_{company}"] = getattr(model, "model_type", "N/A")
                    status.update(label="Scoring complete", state="complete")
            except Exception as e:
                st.error(f"Scoring failed: {e}")

    # Display credit result
    credit_result = st.session_state.get(f"predict_credit_result_{company}")
    credit_shap = st.session_state.get(f"predict_credit_shap_{company}")
    if credit_result is not None:
        _display_credit_result(credit_result, credit_shap, company)

    # -- Demand forecast tab ----------------------------------------------
    with tab_demand:
        forecast_df = _build_forecast_record()

        # Model selection for forecast
        selected_forecast_meta = model_select_from_registry(
            registry, company, "forecast",
            key="pred_forecast_model",
            label="Model type (override)",
        )

        if st.button("Forecast demand", type="primary", key="pred_forecast_demand"):
            try:
                with st.status("Forecasting demand...", expanded=True) as status:
                    # Load the selected model version (defaults to active)
                    if selected_forecast_meta:
                        version, source_company = selected_forecast_meta
                        model, _ = registry.load_by_version(source_company, "forecast", version)
                    else:
                        model, _ = registry.load_latest_with_admin_fallback(company, "forecast")

                    # Ensure all forecast fields exist
                    required = FORECAST_FIELDS
                    for f in required:
                        if f not in forecast_df.columns:
                            if f == "units_sold":
                                forecast_df[f] = 0.0
                            elif f in ("inventory_level",):
                                forecast_df[f] = 0.0
                            else:
                                forecast_df[f] = ""

                    # Convert numeric columns
                    for col in forecast_df.columns:
                        if col in ("units_sold", "inventory_level"):
                            forecast_df[col] = pd.to_numeric(forecast_df[col], errors="coerce").fillna(0.0)

                    featured = model.create_features(forecast_df)
                    met = model.evaluate_featured(featured)
                    result = model.detect_anomalies(forecast_df)

                    shap_results = compute_shap_values(model.model, featured, top_k=8)

                    profile = profiles.load(company)
                    policy = RecommendationPolicy()

                    result["recommended_actions"] = [
                        " | ".join(
                            policy.apply(
                                {"recommended_actions": recommender.forecast(row)},
                                profile,
                            )["recommended_actions"]
                        )
                        for _, row in result.iterrows()
                    ]
                    st.session_state[f"predict_forecast_result_{company}"] = (met, result)
                    st.session_state[f"predict_forecast_shap_{company}"] = shap_results
                    st.session_state[f"predict_forecast_model_type_{company}"] = getattr(model, "model_type", "N/A")
                    status.update(label="Forecast complete", state="complete")
            except Exception as e:
                st.error(f"Forecast failed: {e}")

    # Display forecast result
    forecast_saved = st.session_state.get(f"predict_forecast_result_{company}")
    forecast_shap = st.session_state.get(f"predict_forecast_shap_{company}")
    if forecast_saved is not None:
        met, result = forecast_saved
        st.markdown("#### Forecast accuracy")
        metric_cards(met, ["MAE", "RMSE", "WAPE", "R2"])
        st.dataframe(result, width='stretch', hide_index=True)
        _display_forecast_result(result, forecast_shap, company)
