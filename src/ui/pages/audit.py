from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.audit import query_events


def render(registry, recommender, profiles, company) -> None:
    """Render the admin audit log viewer page."""

    st.markdown(
        '<div class="page-header"><h1>Audit log</h1>'
        '<p class="lead">Append-only record of security-relevant and operational events. '
        'Every login, training run, model activation, and policy change is recorded with '
        'a timestamp, user identity, and event detail.</p></div>',
        unsafe_allow_html=True,
    )

    # -- Filters ---------------------------------------------------------------
    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        event_filter = st.selectbox(
            "Filter by event type",
            ["All", "auth.sign_in", "auth.sign_in_fail", "auth.sign_up",
             "auth.sign_out", "model.train", "model.activate", "policy.update"],
            key="audit_event_filter",
        )
    with col_b:
        user_filter = st.text_input(
            "Filter by username",
            placeholder="e.g. admin",
            key="audit_user_filter",
        )
    with col_c:
        limit = st.number_input("Max rows", 10, 500, 100, key="audit_limit")

    # -- Query and display -----------------------------------------------------
    event_type = None if event_filter == "All" else event_filter
    username = user_filter.strip() or None
    events = query_events(event_type=event_type, username=username, limit=limit)

    if not events:
        st.info("No audit events match the current filters.")
        return

    st.caption(f"Showing {len(events)} event(s), newest first.")

    # Flatten detail JSON for display
    rows = []
    for e in events:
        row = {
            "ID": e["id"],
            "Timestamp": e["timestamp"],
            "Event": e["event_type"],
            "User": e["username"],
            "Role": e["role"],
            "Workspace": e["company_id"],
        }
        detail = e.get("detail")
        if isinstance(detail, dict):
            row["Detail"] = " | ".join(f"{k}: {v}" for k, v in detail.items())
        elif detail:
            row["Detail"] = str(detail)
        else:
            row["Detail"] = ""
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
