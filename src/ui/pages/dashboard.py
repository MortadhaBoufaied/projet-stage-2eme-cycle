from __future__ import annotations
import streamlit as st
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the dashboard page."""

    st.markdown(
        '<div class="page-header"><h1>Dashboard</h1>'
        '<p class="lead">High-level view of platform status and active model performance. '
        'This page does not run predictions -- it shows what has been trained and deployed.</p></div>',
        unsafe_allow_html=True,
    )

    def active(task):
        """Load the metadata for the currently active model version, or None."""
        try:
            return registry.load_latest(company, task)[1]
        except Exception:
            return None

    credit_model = active("credit")
    forecast_model = active("forecast")

    st.markdown("#### Platform status")
    st.caption(
        "Shows whether each model family has a trained, activated version ready for live predictions."
    )
    metric_cards(
        {
            "platform": "Centralized",
            "credit_model": "Ready" if credit_model else "Not trained",
            "demand_model": "Ready" if forecast_model else "Not trained",
            "approval": "Required",
        },
        ["platform", "credit_model", "demand_model", "approval"],
    )

    st.markdown("---")

    st.markdown(
        '<div class="section-head"><h2>Active model performance</h2>'
        '<small>Holdout evaluation metrics from the most recently activated version</small></div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Credit risk model")
        st.caption(
            "Classifier that scores each customer record with a risk probability (0-1) "
            "and assigns a tier. Higher ROC-AUC and Recall indicate better discrimination."
        )
        if credit_model:
            metric_cards(credit_model.get("metrics", {}), ["ROC_AUC", "F1_Score", "Recall"])
            st.caption(f"Active version: {credit_model.get('version', 'Unknown')}")
        else:
            st.info(
                "No active credit model. Go to Training > Credit risk to train one. "
                "The first trained version is automatically activated."
            )

    with right:
        st.markdown("#### Demand forecast model")
        st.caption(
            "Regressor that predicts unit demand per period. Lower MAE and RMSE, "
            "and higher R2, indicate a more accurate forecast."
        )
        if forecast_model:
            metric_cards(forecast_model.get("metrics", {}), ["MAE", "WAPE", "R2"])
            st.caption(f"Active version: {forecast_model.get('version', 'Unknown')}")
        else:
            st.info(
                "No active demand model. Go to Training > Demand to train one. "
                "The first trained version is automatically activated."
            )
