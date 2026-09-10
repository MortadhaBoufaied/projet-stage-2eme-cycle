from __future__ import annotations
import streamlit as st

PAGES = [
    ("dashboard", "bi-speedometer2", "Dashboard"),
    ("credit", "bi-graph-up-arrow", "Credit risk"),
    ("demand", "bi-graph-down-arrow", "Demand"),
    ("training", "bi-tools", "Training"),
    ("policies", "bi-journal-text", "Policies"),
    ("history", "bi-clock-history", "History"),
    ("help", "bi-question-circle", "Help"),
]

PAGE_TITLES = {key: label for key, _, label in PAGES}


def render_sidebar() -> str:
    """Render the icon sidebar and header bar. Returns the selected page key."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    current = st.session_state["current_page"]

    with st.sidebar:
        # Logo
        st.markdown(
            '<div class="sidebar-logo">'
            '<i class="bi bi-graph-up-arrow"></i>'
            '<p>FDS</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Navigation buttons
        for key, icon, label in PAGES:
            is_active = key == current
            btn_label = f'<i class="bi {icon}"></i>  {label}'
            if st.button(
                btn_label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["current_page"] = key
                st.rerun()

        # Divider + sign out
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        from src.services.auth import current_user, sign_out
        user = current_user() or "admin"
        st.caption(f"Signed in as {user}")
        if st.button("Sign out", key="sidebar_signout", use_container_width=True):
            sign_out()
            st.rerun()

    # Header bar
    title = PAGE_TITLES.get(current, "Finance Decision Studio")
    initial = (current_user() or "admin")[0].upper()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:0.6rem 0 1rem; border-bottom:1px solid var(--border); margin-bottom:1.5rem;">
            <h1 style="margin:0; font-size:1.4rem;">{title}</h1>
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="width:32px; height:32px; border-radius:50%; background:var(--accent);
                            color:#fff; display:flex; align-items:center; justify-content:center;
                            font-size:0.85rem; font-weight:600;">{initial}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return current
