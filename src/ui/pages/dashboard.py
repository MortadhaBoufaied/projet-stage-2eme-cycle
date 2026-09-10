from __future__ import annotations
import streamlit as st
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the dashboard page."""
    st.markdown(
        '<div class="page-header"><h1>Dashboard</h1>'
        '<p class="lead">Build governed models, review operational signals, and translate model output into accountable decisions.</p></div>',
        unsafe_allow_html=True,
    )

    def active(task):
        try:
            return registry.load_latest(company, task)[1]
        except Exception:
            return None

    credit_model = active("credit")
    forecast_model = active("forecast")

    metric_cards(
        {"platform": "Centralized", "credit_model": "Ready" if credit_model else "Not trained", "demand_model": "Ready" if forecast_model else "Not trained", "approval": "Required"},
        ["platform", "credit_model", "demand_model", "approval"],
    )

    st.markdown('<div class="section-head"><h2>Model readiness</h2><small>Admin-owned platform metrics</small></div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Credit")
        st.caption("Portfolio risk model")
        if credit_model:
            metric_cards(credit_model.get("metrics", {}), ["ROC_AUC", "F1_Score", "Recall"])
            st.caption(f"Active version: {credit_model.get('version', 'Unknown')}")
        else:
            st.info("No active credit model. Use Training to create one.")
    with right:
        st.markdown("#### Demand")
        st.caption("Historical signal model")
        if forecast_model:
            metric_cards(forecast_model.get("metrics", {}), ["MAE", "WAPE", "R2"])
            st.caption(f"Active version: {forecast_model.get('version', 'Unknown')}")
        else:
            st.info("No active demand model. Use Training to create one.")
