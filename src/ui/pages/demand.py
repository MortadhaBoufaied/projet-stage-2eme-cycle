from __future__ import annotations

import streamlit as st

from src.services.schema import (
    FORECAST_FIELDS,
    apply_mapping,
    validate_forecast,
    quality_report,
)
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the demand analysis page."""

    st.markdown(
        '<div class="page-header"><h1>Demand analysis</h1>'
        '<p class="lead">Evaluate historical demand records against the active forecast model. '
        'The model generates per-period demand predictions, flags anomalies (unusual spikes or '
        'drops), and identifies stockout risk. Governance-filtered supply-chain recommendations '
        'are attached to each flagged record.</p></div>',
        unsafe_allow_html=True,
    )
    st.info(
        "This page runs the **active model** saved on the History page. "
        "It compares actuals to the model's predictions for already-completed periods. "
        "It is not a forward-looking multi-step forecast."
    )

    df = csv_uploader(
        "Historical demand data",
        "forecast_eval",
        help="Upload a CSV of historical demand records. Required columns depend on the "
        "field mapping configured in Training. At minimum, include a date column and a "
        "units-sold or quantity column for each period.",
    )
    if df is None:
        return

    # -- Data summary --------------------------------------------------------
    st.markdown("#### Data summary")
    st.caption(
        "Quick quality check before mapping. Duplicate rows and missing cells may "
        "reduce forecast accuracy."
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
        "before evaluating."
    )
    mp, errs = field_mapping(df, FORECAST_FIELDS, "fe")
    mapped = apply_mapping(df, mp)

    # -- Validation ----------------------------------------------------------
    st.markdown("#### Validation")
    st.caption(
        "Structural checks on the mapped dataset: required fields present, sufficient rows, "
        "no invalid value types. Blocking errors must be resolved before evaluation."
    )
    validation = validate_forecast(mapped, True)
    for e in validation:
        st.error(e)

    # -- Run evaluation ------------------------------------------------------
    if st.button(
        "Evaluate signals",
        type="primary",
        disabled=bool(errs or validation),
        help="Run the active forecast model on the mapped and validated data. "
        "Results include per-period predictions, evaluation metrics (MAE, RMSE, WAPE, R2), "
        "anomaly flags, and stockout risk indicators.",
    ):
        try:
            with st.status("Evaluating demand signals...", expanded=True) as status:
                model, _ = registry.load_latest_with_admin_fallback(company, "forecast")
                featured = model.create_features(mapped)
                met = model.evaluate_featured(featured)
                result = model.detect_anomalies(mapped)
                result["recommended_actions"] = [
                    " | ".join(recommender.forecast(row))
                    for _, row in result.iterrows()
                ]
                st.session_state[f"forecast_result_{company}"] = (met, result)
                status.update(label="Evaluation complete", state="complete")
        except Exception as e:
            st.error(f"Demand evaluation failed: {e}")

    # -- Display results -----------------------------------------------------
    saved = st.session_state.get(f"forecast_result_{company}")
    if saved is None:
        return

    met, result = saved

    st.markdown("#### Forecast accuracy")
    st.caption(
        "Holdout evaluation metrics. Lower MAE and RMSE and higher R2 indicate "
        "better predictive accuracy. WAPE (Weighted Absolute Percentage Error) "
        "is scale-independent and useful for comparing across product lines."
    )
    metric_cards(met, ["MAE", "RMSE", "WAPE", "R2"])

    st.markdown("#### Actual vs predicted")
    st.caption(
        "Stacked line chart comparing actual units sold to the model's predicted values "
        "per period. Divergences signal model drift or data quality issues."
    )
    st.line_chart(
        result.groupby("date")[["units_sold", "forecast_units_sold"]].sum(),
        height=320,
    )

    alerts = result[(result.is_anomaly == 1) | (result.is_stockout_risk == 1)]

    st.markdown("#### Anomalies and stockout risk")
    st.caption(
        "Records flagged as anomalous (unusual spike or drop relative to the model's "
        "expectation) or at stockout risk (predicted demand exceeds available supply "
        "threshold). These rows include governance-filtered recommendations."
    )
    metric_cards(
        {
            "anomalies": int(result.is_anomaly.sum()),
            "stockout_risks": int(result.is_stockout_risk.sum()),
        },
        ["anomalies", "stockout_risks"],
    )

    st.dataframe(alerts, use_container_width=True, hide_index=True)
    st.download_button(
        "Download demand report",
        result.to_csv(index=False).encode(),
        "demand_analysis.csv",
        "text/csv",
        help="Export the full evaluated dataset as CSV including actuals, predictions, "
        "anomaly flags, stockout risk indicators, and recommended actions.",
    )
