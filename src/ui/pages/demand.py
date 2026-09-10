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
        '<p class="lead">Evaluate completed historical periods and identify unusual movement or inventory exposure.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("This is historical evaluation, not a future multi-step forecast.")

    df = csv_uploader("Historical demand data", "forecast_eval")
    if df is None:
        return

    # -- Data summary --------------------------------------------------------
    q = quality_report(df)
    metric_cards(
        q,
        ["rows", "columns", "duplicate_rows", "missing_cells"],
    )
    with st.expander("Preview uploaded data"):
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        st.caption(f"Missing data: {q['missing_percent']:.2f}%")

    # -- Field mapping -------------------------------------------------------
    mp, errs = field_mapping(df, FORECAST_FIELDS, "fe")
    mapped = apply_mapping(df, mp)

    # -- Validation ----------------------------------------------------------
    validation = validate_forecast(mapped, True)
    for e in validation:
        st.error(e)

    # -- Run evaluation ------------------------------------------------------
    if st.button(
        "Evaluate signals",
        type="primary",
        disabled=bool(errs or validation),
    ):
        try:
            with st.status("Evaluating demand signals...", expanded=True) as status:
                model, _ = registry.load_latest(company, "forecast")
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
            st.exception(f"Demand evaluation failed: {e}")

    # -- Display results -----------------------------------------------------
    saved = st.session_state.get(f"forecast_result_{company}")
    if saved is None:
        return

    met, result = saved
    metric_cards(met, ["MAE", "RMSE", "WAPE", "R2"])

    st.line_chart(
        result.groupby("date")[["units_sold", "forecast_units_sold"]].sum(),
        height=320,
    )

    alerts = result[(result.is_anomaly == 1) | (result.is_stockout_risk == 1)]
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
    )
