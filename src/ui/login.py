from __future__ import annotations

import streamlit as st

from src.services.auth import credentials_configured, sign_in, sign_up


def render_login() -> None:
    """Render the split-panel login page with sign-up toggle."""

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

    # -- Initialize view state ------------------------------------------------
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"

    # -- Left branding panel + right auth panel -------------------------------
    left_spacer, center, right_spacer = st.columns([1, 1.6, 1])
    with center:
        panel_left, panel_right = st.columns([2, 3])

        with panel_left:
            st.markdown(
                """
                <div class="login-panel">
                    <i class="bi bi-graph-up-arrow" style="font-size:2rem; color:var(--accent); margin-bottom:1rem;"></i>
                    <h2 style="font-size:1.1rem; font-weight:600; color:var(--text); margin-bottom:0.5rem;">
                        Finance Decision Studio
                    </h2>
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.3rem;">
                        Governed credit risk and demand analysis
                    </p>
                    <p style="font-size:0.8rem; color:var(--text-muted);">
                        Built for teams that need human oversight.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with panel_right:
            # -- Toggle between login and sign-up ----------------------------
            is_login = st.session_state["auth_view"] == "login"

            if is_login:
                _render_login_form()
            else:
                _render_signup_form()


def _render_login_form() -> None:
    """Render the sign-in form."""
    st.markdown(
        "<div style='padding: 1rem 0;'>"
        "<h2 style='font-size:1.2rem; font-weight:600; color:var(--text);'>Welcome back</h2>"
        "<p style='font-size:0.85rem; color:var(--text-muted);'>Sign in to your account</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not credentials_configured():
        st.error(
            "Administrator credentials are missing. Add ADMIN_USERNAME and ADMIN_PASSWORD "
            "to the project .env file, then restart the app."
        )
        st.stop()

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            placeholder="admin",
            autocomplete="username",
        )
        password = st.text_input(
            "Password",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("Sign in", type="primary", width='stretch')

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
                    st.error("The username or password is incorrect.")

    st.caption("Session expires automatically after inactivity.")

    st.markdown("---")
    if st.button("Create an account", key="goto_signup", width='stretch'):
        st.session_state["auth_view"] = "signup"
        st.rerun()


def _render_signup_form() -> None:
    """Render the sign-up form."""
    st.markdown(
        "<div style='padding: 1rem 0;'>"
        "<h2 style='font-size:1.2rem; font-weight:600; color:var(--text);'>Create an account</h2>"
        "<p style='font-size:0.85rem; color:var(--text-muted);'>Register a new user for this workspace</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form("signup_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            placeholder="Choose a username",
            autocomplete="username",
        )
        password = st.text_input(
            "Password",
            type="password",
            help="At least 6 characters.",
            autocomplete="new-password",
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            autocomplete="new-password",
        )
        submitted = st.form_submit_button("Create account", type="primary", width='stretch')

    if submitted:
        if not username.strip() or not password:
            st.error("Enter a username and password.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            try:
                ok, msg = sign_up(username, password)
            except Exception as exc:
                st.error(f"Registration error: {exc}")
            else:
                if ok:
                    st.success(msg)
                    st.session_state["auth_view"] = "login"
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("---")
    if st.button("Back to sign in", key="goto_login", width='stretch'):
        st.session_state["auth_view"] = "login"
        st.rerun()
