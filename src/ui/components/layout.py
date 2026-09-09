from __future__ import annotations
import streamlit as st
from src.ui.theme import apply_light_theme


def page_header(kicker: str, title: str, description: str) -> None:
    """Render a consistent page header with kicker, heading, and caption."""
    st.markdown(
        f'<div class="page-header"><div class="kicker">{kicker}</div>'
        f'<h1>{title}</h1><p class="lead">{description}</p></div>',
        unsafe_allow_html=True,
    )


def section_head(heading: str, subtitle: str = "") -> None:
    """Render a section heading with an optional subtitle."""
    if subtitle:
        st.markdown(f'<div class="section-head"><h2>{heading}</h2><small>{subtitle}</small></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-head"><h2>{heading}</h2></div>', unsafe_allow_html=True)


def two_columns() -> tuple:
    """Return two equally sized columns."""
    return st.columns(2)


def three_columns() -> tuple:
    """Return three equally sized columns."""
    return st.columns(3)


def metric_cards(values: dict, labels: list[str]) -> None:
    """Render a row of metric cards from a dict and ordered label list."""
    cols = st.columns(len(labels))
    for col, name in zip(cols, labels):
        val = values.get(name, "—")
        if isinstance(val, float):
            val = f"{val:.3f}" if abs(val) < 10 else f"{val:.2f}"
        col.metric(name.replace("_", " "), val)


def rule_card(kicker: str, heading: str, body: str = "") -> None:
    """Render a bordered card with a kicker, heading, and optional body."""
    html = f'<div class="rule-card"><div class="kicker">{kicker}</div><h3>{heading}</h3>'
    if body:
        html += f'<p>{body}</p>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def empty_state(icon: str, title: str, description: str) -> None:
    """Render a centered empty-state illustration using Streamlit columns."""
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.markdown(f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{description}</p>
        </div>""", unsafe_allow_html=True)


def status_message(kind: str, text: str) -> None:
    """Render a styled status banner."""
    cls = {"success": "status-success", "warning": "status-warning", "error": "status-error", "info": "status-info"}.get(kind, "status-info")
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)
