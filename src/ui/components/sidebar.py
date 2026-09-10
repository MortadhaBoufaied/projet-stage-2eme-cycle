from __future__ import annotations

import streamlit as st

from src.services.auth import current_user, sign_out

# Navigation is grouped by user intent rather than technical implementation.
NAV_GROUPS = [
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

PAGE_TITLES = {
    item[0]: item[2]
    for _, items in NAV_GROUPS
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
    user = current_user() or "admin"
    initial = user[0].upper()

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-mark">F</div>
                <div>
                    <div class="sidebar-brand-name">FDS</div>
                    <div class="sidebar-brand-subtitle">Finance Decision Studio</div>
                </div>
            </div>
            <div class="sidebar-workspace">
                <span class="sidebar-workspace-label">WORKSPACE</span>
                <strong>Administrator</strong>
                <span>admin_company</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for group_name, items in NAV_GROUPS:
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
                    <span>Administrator</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return current
