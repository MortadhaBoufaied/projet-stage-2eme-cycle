from __future__ import annotations
import streamlit as st
from src.services.auth import credentials_configured, sign_in


def render_login() -> None:
    """Render the split-panel login page."""
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] > .main {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            padding: 2rem !important;
        }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stHeader"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not credentials_configured():
        st.error("Administrator credentials are missing. Add ADMIN_USERNAME and ADMIN_PASSWORD to the project .env file, then restart the app.")
        st.stop()

    left_spacer, center, right_spacer = st.columns([1, 1.6, 1])
    with center:
        panel_left, panel_right = st.columns([2, 3])

        with panel_left:
            st.markdown(
                """
                <div class="login-panel">
                    <i class="bi bi-graph-up-arrow" style="font-size:2rem; color:var(--accent); margin-bottom:1rem;"></i>
                    <h2 style="font-size:1.1rem; font-weight:600; color:var(--text); margin-bottom:0.5rem;">Finance Decision Studio</h2>
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.3rem;">Governed credit risk and demand analysis</p>
                    <p style="font-size:0.8rem; color:var(--text-muted);">Built for teams that need human oversight.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with panel_right:
            st.markdown("<div style='padding: 1rem 0;'><h2 style='font-size:1.2rem; font-weight:600; color:var(--text);'>Welcome back</h2></div>", unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Email or username", placeholder="admin@example.com", autocomplete="username")
                password = st.text_input("Password", type="password", autocomplete="current-password")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("Enter both your username and password.")
                else:
                    try:
                        auth_ok = sign_in(username, password)
                    except Exception as exc:
                        st.error(f"Login error: {exc}")
                    else:
                        if auth_ok:
                            st.rerun()
                        else:
                            st.error("The username or password is incorrect. Check your .env settings and try again.")

            st.caption("Session expires automatically after inactivity.")
