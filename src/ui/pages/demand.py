from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the analyze demand page."""
    st.markdown(
        '<div class="page-header"><h1>Demand analysis</h1>'
        '<p class="lead">Evaluate completed historical periods and identify unusual movement or inventory exposure.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Demand analysis — full implementation coming in Task 7.")
