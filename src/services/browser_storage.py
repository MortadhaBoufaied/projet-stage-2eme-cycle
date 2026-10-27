from __future__ import annotations

import streamlit as st

try:
    from streamlit_js_eval import streamlit_js_eval
except Exception:
    streamlit_js_eval = None

KEY = "finance_remember_token"
_CACHE_KEY = "_finance_browser_token_cache"
_READ_DONE_KEY = "_finance_browser_token_read_done"


def get_token():
    """Read the browser token at most once during a Streamlit script run.

    streamlit-js-eval creates a Streamlit element. Calling it twice with the
    same key in one run raises StreamlitDuplicateElementKey, so subsequent
    callers receive the cached value instead of creating a second element.
    """
    cached = st.session_state.get(_CACHE_KEY)
    if cached:
        return cached
    if streamlit_js_eval is None or st.session_state.get(_READ_DONE_KEY):
        return None
    st.session_state[_READ_DONE_KEY] = True
    token = streamlit_js_eval(
        js_expressions=f'localStorage.getItem("{KEY}")',
        key="read_remember_token",
    )
    if token:
        st.session_state[_CACHE_KEY] = token
    return token


def set_token(token):
    if not token:
        return
    st.session_state[_CACHE_KEY] = token
    if streamlit_js_eval is not None:
        streamlit_js_eval(
            js_expressions=f'localStorage.setItem("{KEY}", {token!r})',
            key="write_remember_token",
        )


def clear_token():
    st.session_state.pop(_CACHE_KEY, None)
    if streamlit_js_eval is not None:
        streamlit_js_eval(
            js_expressions=f'localStorage.removeItem("{KEY}")',
            key="clear_remember_token",
        )
