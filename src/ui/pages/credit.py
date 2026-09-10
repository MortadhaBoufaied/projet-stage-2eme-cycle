from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the analyze credit risk page."""
    st.markdown(
        '<div class="page-header"><h1>Credit risk</h1>'
        '<p class="lead">Upload current customer records. The active saved model runs without retraining.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Credit risk analysis — full implementation coming in Task 6.")
