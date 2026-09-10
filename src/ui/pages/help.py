from __future__ import annotations
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the help page."""
    st.markdown(
        '<div class="page-header"><h1>About</h1>'
        '<p class="lead">A concise guide to the system boundaries and operating model.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("""1. Choose a company workspace.
2. Train with validated historical data.
3. Review holdout metrics before operational use.
4. Analyze current records without retraining.
5. Require human review for consequential recommendations.
6. Use Model versions to inspect or reactivate prior models.""")
