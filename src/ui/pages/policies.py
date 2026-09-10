from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the company policies page."""
    st.markdown(
        '<div class="page-header"><h1>Company rules</h1>'
        '<p class="lead">Personalize recommendations without changing model predictions.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Company policies — full implementation coming in Task 9.")
