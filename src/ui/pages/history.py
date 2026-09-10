from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the model history page."""
    st.markdown(
        '<div class="page-header"><h1>Model versions</h1>'
        '<p class="lead">Inspect saved versions and choose the active model for each workflow.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Model history — full implementation coming in Task 9.")
