from __future__ import annotations

import pandas as pd
import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the model history page."""

    st.markdown(
        '<div class="page-header"><h1>Model versions</h1>'
        '<p class="lead">Inspect saved versions and choose the active model for each workflow.</p></div>',
        unsafe_allow_html=True,
    )

    for task in ["credit", "forecast"]:
        st.markdown(f"### {task.title()}")
        versions = registry.versions(company, task)
        if not versions:
            st.info("No saved versions.")
            continue

        rows = [
            {
                "version": v["version"],
                "saved_at": v["saved_at_utc"],
                **{
                    k: value
                    for k, value in v.get("metrics", {}).items()
                    if isinstance(value, (int, float, str))
                },
            }
            for v in versions
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        chosen = st.selectbox(
            "Activate version",
            [v["version"] for v in versions],
            key=f"version_{task}",
        )
        if st.button("Set active", key=f"activate_{task}"):
            registry.activate(company, task, chosen)
            st.success("Active model updated.")
