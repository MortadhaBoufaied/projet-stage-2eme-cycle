from __future__ import annotations

import streamlit as st

from src.services.auth import current_user, current_role, current_company, sign_out

# Navigation grouped by user intent.  Admin sees all groups; company users
# see only the "Workspace" group (analysis pages).
NAV_GROUPS_ADMIN = [
    (
        "Workspace",
        [
            ("dashboard", "▣", "Dashboard", "Overview and model status"),
            ("credit", "↗", "Credit risk", "Assess credit applications"),
            ("demand", "↘", "Demand", "Forecast historical demand"),
        ],
    ),
    (
        "Models & governance",
        [
            ("training", "⚒", "Training", "Train and compare models"),
            ("policies", "≡", "Policies", "Business rules and thresholds"),
            ("history", "⧖", "History", "Review model versions"),
        ],
    ),
    (
        "Support",
        [
            ("help", "?", "Help", "How the decision workflow works"),
        ],
    ),
]

NAV_GROUPS_COMPANY = [
    (
        "Workspace",
        [
            ("dashboard", "▣", "Dashboard", "Overview and analysis history"),
            ("credit", "↗", "Credit risk", "Assess credit applications"),
            ("demand", "↘", "Demand", "Forecast historical demand"),
        ],
    ),
]

# All pages known to the app, for validating the current selection
ALL_PAGE_KEYS = {item[0] for _, items in NAV_GROUPS_ADMIN for item in items}

# Company-visible pages, for redirecting if a company user lands on a
# restricted page (e.g. via a stale bookmark).
COMPANY_PAGE_KEYS = {item[0] for _, items in NAV_GROUPS_COMPANY for item in items}

PAGE_TITLES = {
    item[0]: item[2]
    for _, items in NAV_GROUPS_ADMIN
    for item in items
}


def _render_nav_item(key: str, icon: str, label: str, description: str, current: str) -> None:
    is_active = key == current
    if st.button(
        f"{icon}  {label}",
        key=f"nav_{key}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
        help=description,
    ):
        st.session_state["current_page"] = key
        st.rerun()


def render_sidebar() -> str:
    """Render grouped navigation and the content header; return the selected page key."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    current = st.session_state["current_page"]
    role = current_role()
    user = current_user() or "admin"
    company = current_company()
    initial = user[0].upper()
    is_admin = role == "admin"
    role_label = "Administrator" if is_admin else "Company"
    nav_groups = NAV_GROUPS_ADMIN if is_admin else NAV_GROUPS_COMPANY

    # Redirect company users away from admin-only pages (e.g. stale bookmark)
    if not is_admin and current not in COMPANY_PAGE_KEYS:
        st.session_state["current_page"] = "dashboard"
        current = "dashboard"

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-brand-mark">F</div>
                <div>
                    <div class="sidebar-brand-name">FDS</div>
                    <div class="sidebar-brand-subtitle">Finance Decision Studio</div>
                </div>
            </div>
            <div class="sidebar-workspace">
                <span class="sidebar-workspace-label">WORKSPACE</span>
                <strong>{role_label}</strong>
                <span>{company}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for group_name, items in nav_groups:
            st.markdown(f'<div class="sidebar-section-label">{group_name}</div>', unsafe_allow_html=True)
            for key, icon, label, description in items:
                _render_nav_item(key, icon, label, description, current)

        st.markdown('<div class="sidebar-footer-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-user"><div class="sidebar-avatar">{initial}</div>'
            f'<div><strong>{user}</strong><span>Signed in</span></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="sidebar_signout", use_container_width=True):
            sign_out()
            st.rerun()

    title = PAGE_TITLES.get(current, "Finance Decision Studio")
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <div class="app-breadcrumb">Finance Decision Studio</div>
                <h1>{title}</h1>
            </div>
            <div class="header-user">
                <div class="header-avatar">{initial}</div>
                <div class="header-user-copy">
                    <strong>{user}</strong>
                    <span>{role_label}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return current
