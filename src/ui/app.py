from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.markdown("""
<style>
[data-testid="stHeader"] {
    display: none;
}

[data-testid="stToolbar"] {
    display: none;
}

footer {
    display: none;
}

#MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

from src.ui.theme import apply_dark_theme
from src.ui.login import render_login
from src.ui.components.sidebar import render_sidebar
from src.ui.pages import PAGE_MAP
from src.services.auth import is_authenticated, current_role, current_company
from src.services.model_registry import ModelRegistry
from src.agents.recommender import RecommendationEngine
from src.services.company_profile import CompanyProfileStore


# -- Page config and theme ---------------------------------------------------
st.set_page_config(
    page_title="Finance Decision Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_dark_theme()


# -- Auth gate ----------------------------------------------------------------
if not is_authenticated():
    render_login()
    st.stop()


# -- Sidebar navigation ------------------------------------------------------
selected_page = render_sidebar()


# -- Clear stale result keys --------------------------------------------------
# Only remove prediction result keys on page navigation.  Training and
# augmentation keys must survive reruns so that trained-model results
# remain visible when the user switches tabs and returns.
keys_to_remove = [
    k
    for k in st.session_state.keys()
    if k.startswith(("credit_result_", "forecast_result_"))
]
for k in keys_to_remove:
    del st.session_state[k]


# -- Shared instances ---------------------------------------------------------
registry = ModelRegistry()
recommender = RecommendationEngine()
profiles = CompanyProfileStore()

# Derive company from the authenticated user's session state.
# Admin (.env login) uses "admin_company"; registered users get their
# own company keyed by username.
company = current_company()

registry.company_dir(company, create=True)
profiles.save(profiles.load(company))


# -- Route to selected page ---------------------------------------------------
PAGE_MAP[selected_page].render(registry, recommender, profiles, company)
