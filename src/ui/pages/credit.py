from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.schema import (
    CREDIT_ID,
    available_credit_fields,
    apply_mapping,
    validate_credit,
    quality_report,
)
from src.services.recommendation_policy import RecommendationPolicy
from src.services.explainer import compute_shap_values
from src.services.nlg import generate_credit_summary
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards, render_shap_bar, render_shap_table


def render(registry, recommender, profiles, company) -> None:
    """Render the credit risk analysis page."""

    st.markdown(
        '<div class="page-header"><h1>Credit risk — Payment Risk Assessment</h1>'
        '<p class="lead"><strong>Agent 2 — Customer & Invoice Delinquency Assessment</strong>: '
        'Assess the probability of delayed payments across customers and invoices using the active credit risk model. '
        'Each account receives a default risk probability (0-1), a risk classification (LOW / MEDIUM / HIGH), '
        'unusual drivers, and managerial credit-control recommendations.</p></div>',
        unsafe_allow_html=True,
    )
    st.info(
        "This agent serves as the **Payment Risk Assessment** intelligence layer for ERP systems. "
        "It supports credit terms assignment, invoice risk monitoring, and proactive collection workflows."
    )

    df = csv_uploader(
        "Customer credit data",
        "credit_predict",
        help="Upload a CSV of customer records. Required columns depend on the field mapping "
        "configured in Training. At minimum, the file should contain financial features "
        "used during model training (e.g. bill amount, payment history, credit limit).",
    )
    if df is None:
        return

    # -- Data summary --------------------------------------------------------
    st.markdown("#### Data summary")
    st.caption(
        "Quick quality check before mapping. Duplicate rows and missing cells may "
        "reduce prediction accuracy."
    )
    q = quality_report(df)
    metric_cards(
        q,
        ["rows", "columns", "duplicate_rows", "missing_cells"],
    )
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25), width='stretch', hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")

    # -- Field mapping -------------------------------------------------------
    st.markdown("#### Field mapping")
    st.caption(
        "Match your CSV columns to the model's expected fields. The system auto-suggests "
        "exact matches and flags alias or invalid-family conflicts. Resolve all errors "
        "before analyzing."
    )
    fields = available_credit_fields(df.columns, False)
    mp, errs = field_mapping(df, fields, "cp_v4")
    mapped = apply_mapping(df, mp)

    # -- Validation ----------------------------------------------------------
    st.markdown("#### Validation")
    st.caption(
        "Structural checks on the mapped dataset: required fields present, sufficient rows, "
        "no invalid value types. Blocking errors must be resolved before analysis."
    )
    validation = validate_credit(mapped, False)
    for e in validation:
        st.error(e)

    # -- Run analysis --------------------------------------------------------
    if st.button(
        "Analyze portfolio",
        type="primary",
        disabled=bool(errs or validation),
        help="Run the active credit model on the mapped and validated data. "
        "Results include risk scores, tier assignments, key indicators, and "
        "governance-filtered recommendations.",
    ):
        try:
            with st.status("Running portfolio analysis...", expanded=True) as status:
                model, _ = registry.load_latest_with_admin_fallback(company, "credit")
                p, tiers = model.predict_risk(mapped)
                explanations = model.explain(mapped)

                # Compute SHAP-based explanations (falls back gracefully if SHAP fails)
                shap_results = compute_shap_values(model.model, mapped, top_k=8)

                # Load company profile to apply governance rules to recommendations
                profile = profiles.load(company)
                policy = RecommendationPolicy()

                identifiers = (
                    mapped[CREDIT_ID].astype(str)
                    if CREDIT_ID in mapped.columns
                    else mapped.index.astype(str)
                )
                result = pd.DataFrame(
                    {
                        CREDIT_ID: identifiers,
                        "risk_score": p,
                        "risk_tier": tiers,
                    }
                )
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
                st.session_state[f"credit_result_{company}"] = result
                st.session_state[f"credit_shap_{company}"] = shap_results
                # Preserve model type for NLG summary context
                st.session_state[f"credit_model_type_{company}"] = getattr(model, "model_type", "N/A")
                status.update(label="Analysis complete", state="complete")
        except Exception as e:
            st.error(f"Portfolio analysis failed: {e}")

    # -- Display results -----------------------------------------------------
    result = st.session_state.get(f"credit_result_{company}")
    if result is None:
        return

    st.markdown("#### Results")
    st.caption(
        "Summary of the scored portfolio. The chart shows tier distribution; "
        "the table lists every record with its risk score, tier, key indicators, "
        "and recommended actions."
    )
    metric_cards(
        {
            "customers": len(result),
            "low": int((result.risk_tier == "LOW_RISK").sum()),
            "medium": int((result.risk_tier == "MEDIUM_RISK").sum()),
            "high": int((result.risk_tier == "HIGH_RISK").sum()),
        },
        ["customers", "low", "medium", "high"],
    )

    chart, table = st.columns([1, 2])
    chart.bar_chart(result.risk_tier.value_counts(), height=300)
    table.dataframe(
        result,
        width='stretch',
        hide_index=True,
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk score", min_value=0, max_value=1, format="%.0f%%"
            )
        },
    )
    st.download_button(
        "Download portfolio report",
        result.to_csv(index=False).encode(),
        "credit_portfolio.csv",
        "text/csv",
        help="Export the full scored portfolio as a CSV file including risk scores, "
        "tiers, key indicators, and recommended actions.",
    )

    # -- SHAP Explainability --------------------------------------------------
    shap_results = st.session_state.get(f"credit_shap_{company}")
    if shap_results is not None:
        st.markdown("#### Model explainability (SHAP)")
        st.caption(
            "SHAP (SHapley Additive exPlanations) values show how each feature contributes "
            "to the risk prediction for individual records. Positive values increase risk; "
            "negative values decrease risk."
        )
        record_idx = st.selectbox(
            "Select a record to explain",
            range(len(result)),
            format_func=lambda i: f"Record {i} -- {result.iloc[i].get(CREDIT_ID, i)} (score: {result.iloc[i]['risk_score']:.2f})",
            key="credit_shap_record",
        )
        indicators = shap_results[record_idx]
        render_shap_bar(indicators, record_label=str(result.iloc[record_idx].get(CREDIT_ID, "")), key_prefix="credit_shap")
        with st.expander("SHAP details table"):
            render_shap_table(indicators)
    elif shap_results is None and result is not None:
        st.info(
            "SHAP explanations are unavailable for the current model. "
            "The system falls back to median-deviation indicators shown in the key_indicators column."
        )

    # -- AI Summary -----------------------------------------------------------
    st.markdown("#### AI Summary")
    st.caption(
        "A natural language summary of the portfolio risk assessment. "
        "Generated by an LLM when an API key is configured; otherwise a "
        "template-based summary is shown."
    )
    records_for_nlg = result.to_dict(orient="records")
    model_type = st.session_state.get(f"credit_model_type_{company}", "N/A")
    nlg_metrics = {"model_type": model_type}
    # Try to pull evaluation metrics from session state if available
    cached_metrics = st.session_state.get(f"credit_eval_metrics_{company}")
    if isinstance(cached_metrics, dict):
        nlg_metrics.update(cached_metrics)
    summary_text = generate_credit_summary(records_for_nlg, nlg_metrics)
    st.markdown(summary_text)
