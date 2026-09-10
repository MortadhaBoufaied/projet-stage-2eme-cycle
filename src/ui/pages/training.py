from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the training page."""
    st.markdown(
        '<div class="page-header"><h1>Training</h1>'
        '<p class="lead">Validate data, train on one partition, evaluate on untouched records, and save a version.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Model training — full implementation coming in Task 8.")
