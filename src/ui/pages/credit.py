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
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the credit risk analysis page."""

    st.markdown(
        '<div class="page-header"><h1>Credit risk</h1>'
        '<p class="lead">Score a portfolio of customer records using the currently active credit model. '
        'Each record receives a risk probability (0-1), a tier classification (LOW / MEDIUM / HIGH), '
        'key risk indicators, and a governance-filtered recommendation.</p></div>',
        unsafe_allow_html=True,
    )
    st.info(
        "This page runs the **active model** saved on the History page. "
        "It does not retrain. Upload new data or re-score existing data at any time."
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
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
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
                model, _ = registry.load_latest(company, "credit")
                p, tiers = model.predict_risk(mapped)
                explanations = model.explain(mapped)

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
                    " | ".join(recommender.credit(x)["recommended_actions"])
                    for x in explanations
                ]
                st.session_state[f"credit_result_{company}"] = result
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
        use_container_width=True,
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
