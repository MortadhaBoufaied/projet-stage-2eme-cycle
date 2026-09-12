from __future__ import annotations
import pandas as pd
import streamlit as st

from src.services.auth import current_role, current_company
from src.ui.components.display import metric_cards


def render(registry, recommender, profiles, company) -> None:
    """Render the dashboard page -- content varies by role."""
    role = current_role()
    if role == "admin":
        _render_admin_dashboard(registry, company)
    else:
        _render_company_dashboard(registry, company)


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

def _render_admin_dashboard(registry, company: str) -> None:
    """Platform status and active model performance for administrators."""
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


# ---------------------------------------------------------------------------
# Company dashboard
# ---------------------------------------------------------------------------

def _render_company_dashboard(registry, company: str) -> None:
    """Workspace overview for company users: model status, quick actions, history."""
    st.markdown(
        '<div class="page-header"><h1>Dashboard</h1>'
        f'<p class="lead">Welcome to your workspace ({company}). '
        "Check which models are available for analysis, or jump straight into "
        "credit risk or demand forecasting.</p></div>",
        unsafe_allow_html=True,
    )

    # -- Active model status --------------------------------------------------
    # Use the admin-fallback variant so company users see admin-trained models.
    def active(task):
        try:
            return registry.load_latest_with_admin_fallback(company, task)[1]
        except Exception:
            return None

    credit_model = active("credit")
    forecast_model = active("forecast")

    st.markdown("#### Available models")
    st.caption(
        "Models trained by the administrator and activated for your workspace. "
        "If a model shows 'Not available', contact the administrator to train one."
    )
    metric_cards(
        {
            "credit_model": "Ready" if credit_model else "Not available",
            "demand_model": "Ready" if forecast_model else "Not available",
        },
        ["credit_model", "demand_model"],
    )

    # -- Quick actions --------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Quick actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Credit risk analysis",
            width='stretch',
            type="primary" if credit_model else "secondary",
            disabled=credit_model is None,
            help="Upload customer data and run it through the active credit risk model.",
        ):
            st.session_state["current_page"] = "credit"
            st.rerun()
        if credit_model:
            st.caption(
                f"Active version: {credit_model.get('version', 'Unknown')}"
            )
        else:
            st.caption("No credit model available yet.")

    with col2:
        if st.button(
            "Demand forecast",
            width='stretch',
            type="primary" if forecast_model else "secondary",
            disabled=forecast_model is None,
            help="Upload historical demand data and run it through the active forecast model.",
        ):
            st.session_state["current_page"] = "demand"
            st.rerun()
        if forecast_model:
            st.caption(
                f"Active version: {forecast_model.get('version', 'Unknown')}"
            )
        else:
            st.caption("No demand model available yet.")

    # -- Recent analysis history ----------------------------------------------
    st.markdown("---")
    st.markdown("#### Recent analyses")
    st.caption("History of models saved for your workspace.")

    has_any = False
    for task, label in [("credit", "Credit risk"), ("forecast", "Demand forecast")]:
        versions = registry.versions(company, task)
        if not versions:
            continue
        has_any = True
        st.markdown(f"**{label}** ({len(versions)} version(s))")
        rows = [
            {
                "version": v["version"],
                "saved_at": v["saved_at_utc"],
                "active": "Yes" if v.get("is_active") else "",
                **{
                    k: val
                    for k, val in v.get("metrics", {}).items()
                    if isinstance(val, (int, float, str))
                },
            }
            for v in versions[:5]
        ]
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    if not has_any:
        st.info(
            "No analyses yet. Once the administrator trains and activates a model, "
            "you can use the Credit risk or Demand forecast pages to run analyses."
        )
