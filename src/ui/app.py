from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

import streamlit.components.v1 as components
from src.ui.theme import apply_dark_theme
from src.ui.login import render_login
from src.ui.components.sidebar import render_sidebar
from src.ui.pages import PAGE_MAP
from src.services.auth import is_authenticated
from src.services.model_registry import ModelRegistry
from src.agents.recommender import RecommendationEngine
from src.services.company_profile import CompanyProfileStore


# -- Page config and theme ---------------------------------------------------
st.set_page_config(
    page_title="Finance Decision Studio",
    page_icon="chart",
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
keys_to_remove = [
    k
    for k in st.session_state.keys()
    if k.startswith(
        ("credit_result_", "forecast_result_", "credit_training_", "augmentation_")
    )
]
for k in keys_to_remove:
    del st.session_state[k]


# -- Shared instances ---------------------------------------------------------
registry = ModelRegistry()
recommender = RecommendationEngine()
profiles = CompanyProfileStore()
company = "admin_company"
registry.company_dir(company, create=True)
profiles.save(profiles.load(company))


# -- Route to selected page ---------------------------------------------------
PAGE_MAP[selected_page].render(registry, recommender, profiles, company)

# -- Fix sidebar expand button: inject JS that forces it visible/clickable ---
components.html(
    """<script>
    (function fixSidebar() {
        // Try every known selector for the sidebar expand/collapse button
        var sels = [
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="stSidebarCollapsedControl"]',
            '[data-testid="collapsedControl"]',
            'button[title="Open sidebar"]',
            'button[title="Close sidebar"]',
            '[aria-label="Open sidebar"]',
            '[aria-label="Close sidebar"]',
            '.collapsed-icon',
            '.expanded-icon',
        ];
        sels.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                el.style.cssText = 'z-index:9999 !important; opacity:1 !important; visibility:visible !important; pointer-events:auto !important; display:flex !important; position:relative !important; cursor:pointer !important;';
                // Also fix parent containers that might hide it
                var p = el.parentElement;
                for (var i = 0; i < 5 && p; i++) {
                    p.style.cssText += ' visibility:visible !important; opacity:1 !important; pointer-events:auto !important; overflow:visible !important; z-index:9999 !important;';
                    p = p.parentElement;
                }
            });
        });
        // Also force the sidebar section section to not clip children
        document.querySelectorAll('[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]').forEach(function(el) {
            el.style.overflow = 'visible';
        });
    })();
    </script>""",
    height=0,
)
