from __future__ import annotations

import streamlit as st

from src.services.schema import (
    FORECAST_FIELDS,
    apply_mapping,
    validate_forecast,
    quality_report,
)
from src.services.recommendation_policy import RecommendationPolicy
from src.services.explainer import compute_shap_values
from src.services.nlg import generate_demand_summary
from src.ui.components.fields import csv_uploader, field_mapping
from src.ui.components.display import metric_cards, render_shap_bar, render_shap_table


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
        "It evaluates historical demand and can project future periods "
        "using iterative multi-step forecasting."
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

                # Compute SHAP explanations on the feature-engineered data.
                # The forecast pipeline wraps a ColumnTransformer, so SHAP
                # aggregates OHE-encoded categorical features back to originals.
                shap_results = compute_shap_values(
                    model.model, featured, top_k=8,
                )

                # Load company profile to apply governance rules to recommendations
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
                st.session_state[f"forecast_result_{company}"] = (met, result)
                st.session_state[f"forecast_shap_{company}"] = shap_results
                # Preserve model type for NLG summary context
                st.session_state[f"forecast_model_type_{company}"] = getattr(model, "model_type", "N/A")
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

    # -- SHAP Explainability --------------------------------------------------
    shap_results = st.session_state.get(f"forecast_shap_{company}")
    if shap_results is not None:
        st.markdown("#### Model explainability (SHAP)")
        st.caption(
            "SHAP values show how each feature contributes to the forecast for "
            "individual periods. Positive values increase predicted demand; "
            "negative values decrease it."
        )
        record_idx = st.selectbox(
            "Select a period to explain",
            range(len(result)),
            format_func=lambda i: (
                f"Period {i} -- {result.iloc[i].get('date', i)} "
                f"(actual: {result.iloc[i].get('units_sold', '?')}, "
                f"predicted: {result.iloc[i].get('forecast_units_sold', '?'):.1f})"
            ),
            key="forecast_shap_record",
        )
        indicators = shap_results[record_idx]
        render_shap_bar(
            indicators,
            record_label=str(result.iloc[record_idx].get("date", "")),
            key_prefix="forecast_shap",
        )
        with st.expander("SHAP details table"):
            render_shap_table(indicators)
    elif shap_results is None and result is not None:
        st.info(
            "SHAP explanations are unavailable for the current forecast model. "
            "The actual vs predicted chart and anomaly flags still provide interpretability."
        )

    # -- AI Summary -----------------------------------------------------------
    st.markdown("#### AI Summary")
    st.caption(
        "A natural language summary of the demand forecast evaluation. "
        "Generated by an LLM when an API key is configured; otherwise a "
        "template-based summary is shown."
    )
    model_type = st.session_state.get(f"forecast_model_type_{company}", "N/A")
    n_anomalies = int(result.is_anomaly.sum())
    n_stockouts = int(result.is_stockout_risk.sum())
    summary_text = generate_demand_summary(met, n_anomalies, n_stockouts, model_type)
    st.markdown(summary_text)

    # -- Forward Projection (Task 6) ------------------------------------------
    st.markdown("#### Forward projection")
    st.caption(
        "Project demand into future periods using iterative multi-step forecasting. "
        "The model predicts the next period, feeds the prediction back as a lag value, "
        "and repeats for the requested horizon."
    )
    with st.form("forward_projection_form"):
        proj_col1, proj_col2 = st.columns(2)
        with proj_col1:
            n_periods = st.selectbox(
                "Projection horizon (days)",
                [7, 14, 30],
                index=1,
                help="Number of future days to project. Longer horizons accumulate "
                "more iterative error.",
            )
        with proj_col2:
            run_projection = st.form_submit_button(
                "Run forward projection",
                type="primary",
                help="Generate a forward-looking demand forecast for the selected horizon.",
            )

    if run_projection:
        try:
            with st.status("Projecting demand forward...", expanded=True) as status:
                model, _ = registry.load_latest_with_admin_fallback(company, "forecast")
                proj = model.predict_forward(mapped, n_periods=n_periods)
                st.session_state[f"forecast_proj_{company}"] = proj
                status.update(label="Projection complete", state="complete")
        except Exception as e:
            st.error(f"Forward projection failed: {e}")

    proj = st.session_state.get(f"forecast_proj_{company}")
    if proj is not None and not proj.empty:
        st.line_chart(
            proj.groupby("date")["predicted_units"].sum(),
            height=300,
        )
        st.dataframe(proj, use_container_width=True, hide_index=True)
        st.download_button(
            "Download projection",
            proj.to_csv(index=False).encode(),
            "demand_projection.csv",
            "text/csv",
            help="Export the forward projection as CSV.",
        )

        # -- Revenue Estimation (Task 7) --------------------------------------
        st.markdown("#### Revenue projection")
        st.caption(
            "Multiply predicted units by the configured per-unit price to "
            "estimate future revenue. Configure the price on the Policies page."
        )
        profile = profiles.load(company)
        price = getattr(profile, "price_per_unit", 1.0)
        st.caption(f"Current unit price: **{price}** {profile.currency}")
        revenue_proj = model.predict_revenue(proj, price_per_unit=price)

        st.bar_chart(
            revenue_proj.groupby("date")["estimated_revenue"].sum(),
            height=300,
        )
        st.dataframe(revenue_proj, use_container_width=True, hide_index=True)
        st.download_button(
            "Download revenue projection",
            revenue_proj.to_csv(index=False).encode(),
            "demand_revenue_projection.csv",
            "text/csv",
            help="Export the revenue projection as CSV.",
        )
