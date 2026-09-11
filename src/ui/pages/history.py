from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.audit import log_event, AuditEvent
from src.services.auth import current_user, current_role


def render(registry, recommender, profiles, company) -> None:
    """Render the model history page."""

    st.markdown(
        '<div class="page-header"><h1>Model versions</h1>'
        '<p class="lead">Every trained model is saved as an immutable version with its metrics, '
        'hyperparameters, and training data summary. Use this page to compare versions and '
        'control which one is active for live predictions.</p></div>',
        unsafe_allow_html=True,
    )

    for task in ["credit", "forecast"]:
        label = "Credit risk" if task == "credit" else "Demand forecast"
        st.markdown(f"### {label}")
        versions = registry.versions(company, task)
        if not versions:
            st.info(
                f"No {label.lower()} models saved yet. "
                "Go to Training to train your first model -- it will appear here automatically."
            )
            continue

        st.caption(
            f"{len(versions)} version(s) saved. The table below shows each version's holdout "
            "evaluation metrics so you can compare performance across training runs."
        )
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
            help="Select a version to make it the active model. "
            "All subsequent predictions on the Credit risk or Demand page will use this version.",
        )
        if st.button(
            "Set active",
            key=f"activate_{task}",
            help="Promote the selected version to active. The previous active version is retained "
            "but no longer used for live predictions.",
        ):
            registry.activate(company, task, chosen)
            log_event(
                AuditEvent.MODEL_ACTIVATE,
                username=current_user(), role=current_role(), company_id=company,
                detail={"task": task, "version": chosen},
            )
            st.success(
                f"Active {label.lower()} model updated to version **{chosen}**. "
                "New predictions will use this version."
            )
