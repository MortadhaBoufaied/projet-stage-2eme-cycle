from __future__ import annotations
import hmac
from datetime import datetime, timedelta, timezone
import streamlit as st
from src.config import ADMIN_PASSWORD, ADMIN_USERNAME, SESSION_MINUTES

_AUTH_KEY = "finance_authenticated"
_USER_KEY = "finance_user"
_EXPIRY_KEY = "finance_session_expiry"


def credentials_configured() -> bool:
    return bool(ADMIN_USERNAME and ADMIN_PASSWORD)


def sign_in(username: str, password: str) -> bool:
    valid = credentials_configured() and hmac.compare_digest(username.strip(), ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)
    if valid:
        st.session_state[_AUTH_KEY] = True
        st.session_state[_USER_KEY] = ADMIN_USERNAME
        st.session_state[_EXPIRY_KEY] = datetime.now(timezone.utc) + timedelta(minutes=SESSION_MINUTES)
    return valid


def is_authenticated() -> bool:
    if not st.session_state.get(_AUTH_KEY, False):
        return False
    expiry = st.session_state.get(_EXPIRY_KEY)
    if not expiry or datetime.now(timezone.utc) >= expiry:
        sign_out()
        return False
    return True


def current_user() -> str:
    return str(st.session_state.get(_USER_KEY, ""))


def sign_out() -> None:
    for key in (_AUTH_KEY, _USER_KEY, _EXPIRY_KEY):
        st.session_state.pop(key, None)
